/**
 * MCP Tools実装モジュール
 * rag_index, rag_delete, rag_sync の実装
 */

import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { promisify } from 'util';
import { exec } from 'child_process';

const execAsync = promisify(exec);

/**
 * ドキュメントメタデータの管理（簡易版）
 * 実際の実装では ChromaDB を使用
 */
class DocumentStore {
  constructor(basePath = '/home/ogura/.rag') {
    this.basePath = basePath;
    this.metadataPath = path.join(basePath, 'metadata.json');
    this.documentsPath = path.join(basePath, 'documents');
    this.loadMetadata();
  }

  loadMetadata() {
    try {
      if (fs.existsSync(this.metadataPath)) {
        const data = fs.readFileSync(this.metadataPath, 'utf8');
        this.metadata = JSON.parse(data);
      } else {
        this.metadata = {
          projects: {},
          documents: {}
        };
      }
    } catch (error) {
      this.metadata = {
        projects: {},
        documents: {}
      };
    }
  }

  saveMetadata() {
    try {
      fs.writeFileSync(this.metadataPath, JSON.stringify(this.metadata, null, 2));
    } catch (error) {
      console.error('Failed to save metadata:', error);
    }
  }

  generateDocId(filePath) {
    return crypto.createHash('md5').update(filePath).digest('hex');
  }
}

/**
 * rag_index Tool の実装
 * ドキュメントをインデックスに追加
 */
export async function executeRagIndex(indexPath, projectId, options = {}) {
  const store = new DocumentStore();
  const { recursive = false, metadata = {}, update = false } = options;
  
  const result = {
    indexed_files: [],
    total_chunks: 0,
    errors: [],
    time_taken_ms: 0
  };
  
  const startTime = Date.now();
  
  try {
    // パスの検証
    if (!fs.existsSync(indexPath)) {
      throw new Error(`Path does not exist: ${indexPath}`);
    }
    
    const stats = fs.statSync(indexPath);
    let filesToIndex = [];
    
    if (stats.isDirectory()) {
      // ディレクトリの場合
      if (recursive) {
        // 再帰的にファイルを取得
        filesToIndex = getAllFiles(indexPath, ['.md', '.txt', '.html']);
      } else {
        // 直下のファイルのみ
        const files = fs.readdirSync(indexPath);
        filesToIndex = files
          .filter(f => ['.md', '.txt', '.html'].some(ext => f.endsWith(ext)))
          .map(f => path.join(indexPath, f));
      }
    } else {
      // 単一ファイル
      filesToIndex = [indexPath];
    }
    
    // プロジェクトの初期化
    if (!store.metadata.projects[projectId]) {
      store.metadata.projects[projectId] = {
        name: projectId,
        created_at: new Date().toISOString(),
        document_count: 0,
        last_updated: new Date().toISOString()
      };
    }
    
    // 各ファイルをインデックス
    for (const filePath of filesToIndex) {
      try {
        const docId = store.generateDocId(filePath);
        const content = fs.readFileSync(filePath, 'utf8');
        const fileStats = fs.statSync(filePath);
        
        // 既存ドキュメントのチェック
        if (store.metadata.documents[docId] && !update) {
          console.log(`Skipping existing document: ${filePath}`);
          continue;
        }
        
        // チャンク分割（簡易版：1000文字ごと）
        const chunks = [];
        const chunkSize = 1000;
        for (let i = 0; i < content.length; i += chunkSize) {
          chunks.push(content.substring(i, i + chunkSize));
        }
        
        // メタデータの保存
        store.metadata.documents[docId] = {
          id: docId,
          file_path: filePath,
          project_id: projectId,
          chunks: chunks.length,
          size: fileStats.size,
          created_at: fileStats.birthtime.toISOString(),
          modified_at: fileStats.mtime.toISOString(),
          indexed_at: new Date().toISOString(),
          ...metadata
        };
        
        result.indexed_files.push(filePath);
        result.total_chunks += chunks.length;
        
        // ChromaDBへの実際の登録はここで行う（未実装）
        // await chromaDB.addDocuments(chunks, docId, projectId);
        
      } catch (error) {
        result.errors.push(`Failed to index ${filePath}: ${error.message}`);
      }
    }
    
    // プロジェクト情報の更新
    store.metadata.projects[projectId].document_count = Object.values(store.metadata.documents)
      .filter(doc => doc.project_id === projectId).length;
    store.metadata.projects[projectId].last_updated = new Date().toISOString();
    
    // メタデータの保存
    store.saveMetadata();
    
  } catch (error) {
    result.errors.push(error.message);
  }
  
  result.time_taken_ms = Date.now() - startTime;
  return result;
}

/**
 * rag_delete Tool の実装
 * ドキュメントを削除
 */
export async function executeRagDelete(options = {}) {
  const store = new DocumentStore();
  const { document_id, project, filters = {} } = options;
  
  const result = {
    deleted_count: 0,
    deleted_ids: []
  };
  
  try {
    let documentsToDelete = [];
    
    if (document_id) {
      // 特定のドキュメントを削除
      if (store.metadata.documents[document_id]) {
        documentsToDelete.push(document_id);
      }
    } else if (project) {
      // プロジェクト全体を削除
      documentsToDelete = Object.keys(store.metadata.documents)
        .filter(docId => store.metadata.documents[docId].project_id === project);
    } else if (filters) {
      // フィルタ条件による削除
      documentsToDelete = Object.keys(store.metadata.documents).filter(docId => {
        const doc = store.metadata.documents[docId];
        
        // older_than フィルタ
        if (filters.older_than) {
          const days = parseInt(filters.older_than);
          const cutoffDate = new Date();
          cutoffDate.setDate(cutoffDate.getDate() - days);
          if (new Date(doc.indexed_at) > cutoffDate) {
            return false;
          }
        }
        
        // category フィルタ
        if (filters.category && doc.category !== filters.category) {
          return false;
        }
        
        // source_type フィルタ
        if (filters.source_type && doc.source_type !== filters.source_type) {
          return false;
        }
        
        return true;
      });
    }
    
    // ドキュメントの削除
    for (const docId of documentsToDelete) {
      delete store.metadata.documents[docId];
      result.deleted_ids.push(docId);
      result.deleted_count++;
      
      // ChromaDBからも削除（未実装）
      // await chromaDB.deleteDocument(docId);
    }
    
    // プロジェクト情報の更新
    if (project && result.deleted_count > 0) {
      if (store.metadata.projects[project]) {
        store.metadata.projects[project].document_count -= result.deleted_count;
        if (store.metadata.projects[project].document_count <= 0) {
          delete store.metadata.projects[project];
        }
      }
    }
    
    // メタデータの保存
    store.saveMetadata();
    
  } catch (error) {
    console.error('Delete error:', error);
  }
  
  return result;
}

/**
 * rag_sync Tool の実装
 * プロジェクトのドキュメントを同期
 */
export async function executeRagSync(project, syncPath, options = {}) {
  const store = new DocumentStore();
  const { full = false, remove_deleted = true } = options;
  
  const result = {
    added: [],
    updated: [],
    deleted: [],
    unchanged: 0
  };
  
  try {
    // 既存ドキュメントの取得
    const existingDocs = Object.values(store.metadata.documents)
      .filter(doc => doc.project_id === project);
    
    // ファイルシステムの現在のファイル
    const currentFiles = getAllFiles(syncPath, ['.md', '.txt', '.html']);
    const currentFilesMap = new Map();
    
    for (const filePath of currentFiles) {
      const docId = store.generateDocId(filePath);
      const stats = fs.statSync(filePath);
      currentFilesMap.set(docId, {
        path: filePath,
        modified: stats.mtime.toISOString()
      });
    }
    
    // 完全再インデックスの場合
    if (full) {
      // 既存のドキュメントをすべて削除
      for (const doc of existingDocs) {
        delete store.metadata.documents[doc.id];
        result.deleted.push(doc.file_path);
      }
      
      // すべてのファイルを再インデックス
      for (const [docId, fileInfo] of currentFilesMap) {
        const indexResult = await executeRagIndex(fileInfo.path, project, { update: true });
        if (indexResult.indexed_files.length > 0) {
          result.added.push(fileInfo.path);
        }
      }
    } else {
      // 差分同期
      const existingDocIds = new Set(existingDocs.map(doc => doc.id));
      
      // 新規・更新ファイルの処理
      for (const [docId, fileInfo] of currentFilesMap) {
        if (!existingDocIds.has(docId)) {
          // 新規ファイル
          const indexResult = await executeRagIndex(fileInfo.path, project);
          if (indexResult.indexed_files.length > 0) {
            result.added.push(fileInfo.path);
          }
        } else {
          // 既存ファイル - 更新チェック
          const existingDoc = store.metadata.documents[docId];
          if (existingDoc.modified_at < fileInfo.modified) {
            // ファイルが更新されている
            const indexResult = await executeRagIndex(fileInfo.path, project, { update: true });
            if (indexResult.indexed_files.length > 0) {
              result.updated.push(fileInfo.path);
            }
          } else {
            result.unchanged++;
          }
        }
      }
      
      // 削除されたファイルの処理
      if (remove_deleted) {
        for (const doc of existingDocs) {
          if (!currentFilesMap.has(doc.id)) {
            // ファイルが存在しない
            delete store.metadata.documents[doc.id];
            result.deleted.push(doc.file_path);
          }
        }
      }
    }
    
    // メタデータの保存
    store.saveMetadata();
    
  } catch (error) {
    console.error('Sync error:', error);
  }
  
  return result;
}

/**
 * フィルタリング機能の実装
 * 検索結果をフィルタリング
 */
export function applyFilters(results, filters) {
  if (!filters || Object.keys(filters).length === 0) {
    return results;
  }
  
  return results.filter(result => {
    const metadata = result.metadata || {};
    
    // カテゴリフィルタ
    if (filters.category && metadata.category !== filters.category) {
      return false;
    }
    
    // タグフィルタ
    if (filters.tags && filters.tags.length > 0) {
      const docTags = metadata.tags || [];
      const hasMatchingTag = filters.tags.some(tag => docTags.includes(tag));
      if (!hasMatchingTag) {
        return false;
      }
    }
    
    // 日付フィルタ
    if (filters.created_after) {
      const createdAt = new Date(metadata.created_at || 0);
      if (createdAt < new Date(filters.created_after)) {
        return false;
      }
    }
    
    if (filters.created_before) {
      const createdAt = new Date(metadata.created_at || 0);
      if (createdAt > new Date(filters.created_before)) {
        return false;
      }
    }
    
    return true;
  });
}

/**
 * 位置情報とハイライトの追加
 */
export function addPositionAndHighlights(results, query) {
  return results.map(result => {
    const text = result.text || '';
    const queryLower = query.toLowerCase();
    const textLower = text.toLowerCase();
    
    // 位置情報の計算（簡易版）
    const lines = text.split('\n');
    let lineStart = 0;
    let lineEnd = lines.length - 1;
    
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].toLowerCase().includes(queryLower)) {
        lineStart = i;
        lineEnd = Math.min(i + 5, lines.length - 1);
        break;
      }
    }
    
    result.position = {
      line_start: lineStart,
      line_end: lineEnd,
      section: extractSection(text, lineStart)
    };
    
    // ハイライトの計算
    const highlights = [];
    let index = 0;
    while ((index = textLower.indexOf(queryLower, index)) !== -1) {
      highlights.push({
        start: index,
        end: index + query.length
      });
      index += query.length;
    }
    
    result.highlights = highlights;
    
    return result;
  });
}

/**
 * ユーティリティ関数
 */
function getAllFiles(dirPath, extensions = []) {
  let files = [];
  
  try {
    const items = fs.readdirSync(dirPath);
    
    for (const item of items) {
      const fullPath = path.join(dirPath, item);
      const stats = fs.statSync(fullPath);
      
      if (stats.isDirectory()) {
        // 再帰的にディレクトリを探索
        files = files.concat(getAllFiles(fullPath, extensions));
      } else if (stats.isFile()) {
        // 拡張子チェック
        if (extensions.length === 0 || extensions.some(ext => fullPath.endsWith(ext))) {
          files.push(fullPath);
        }
      }
    }
  } catch (error) {
    console.error(`Error reading directory ${dirPath}:`, error);
  }
  
  return files;
}

function extractSection(text, lineNumber) {
  const lines = text.split('\n');
  
  // 直前の見出しを探す
  for (let i = lineNumber; i >= 0; i--) {
    if (lines[i].match(/^#+\s/)) {
      return lines[i].replace(/^#+\s/, '').trim();
    }
  }
  
  return null;
}

export default {
  executeRagIndex,
  executeRagDelete,
  executeRagSync,
  applyFilters,
  addPositionAndHighlights
};