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
const RAG_CMD = '/home/ogura/.rag/venv/bin/rag';

/**
 * ChromaDBを使用した実際のインデックス実装
 */
export async function executeRagIndex(indexPath, projectId, options = {}) {
  const { recursive = false, metadata = {}, update = false } = options;
  
  const result = {
    indexed_files: [],
    total_files: 0,
    skipped_files: 0,
    errors: [],
    time_taken_ms: 0
  };
  
  const startTime = Date.now();
  
  try {
    // パスの検証
    if (!fs.existsSync(indexPath)) {
      throw new Error(`Path does not exist: ${indexPath}`);
    }
    
    // CLIツールのindexコマンドを使用
    let cmd = `${RAG_CMD} index "${indexPath}" --project "${projectId}" --format json`;
    
    if (recursive) {
      cmd += ' --recursive';
    }
    if (update) {
      cmd += ' --update';
    }
    
    const { stdout, stderr } = await execAsync(cmd, {
      maxBuffer: 1024 * 1024 * 10, // 10MB buffer
      env: { ...process.env, PYTHONPATH: '/home/ogura/.rag/src' }
    });
    
    if (stderr) {
      console.error('Index stderr:', stderr);
    }
    
    // 結果をパース
    try {
      const cliResult = JSON.parse(stdout);
      result.indexed_files = cliResult.indexed || 0;
      result.skipped_files = cliResult.skipped || 0;
      result.total_files = cliResult.total_files || 0;
      
      if (cliResult.error) {
        result.errors.push(cliResult.error.message);
      }
    } catch (parseError) {
      // JSON以外の出力の場合
      console.log('Index output:', stdout);
      result.indexed_files = 1; // 仮の値
    }
    
  } catch (error) {
    result.errors.push(error.message);
    throw error;
  }
  
  result.time_taken_ms = Date.now() - startTime;
  return result;
}

/**
 * rag_delete Tool の実装
 */
export async function executeRagDelete(options = {}) {
  const { document_id, project, filters = {} } = options;
  
  const result = {
    deleted_count: 0,
    deleted_ids: [],
    error: null
  };
  
  try {
    // TODO: CLIにdeleteコマンドを追加後、ここで呼び出す
    // 現時点では未実装
    result.error = "Delete functionality not yet implemented in CLI";
    
  } catch (error) {
    result.error = error.message;
  }
  
  return result;
}

/**
 * rag_sync Tool の実装
 */
export async function executeRagSync(projectId, syncPath, options = {}) {
  const { full = false, remove_deleted = true } = options;
  
  const result = {
    added: 0,
    updated: 0,
    deleted: 0,
    errors: [],
    time_taken_ms: 0
  };
  
  const startTime = Date.now();
  
  try {
    // indexコマンドを使用して同期
    let cmd = `${RAG_CMD} index "${syncPath}" --project "${projectId}" --recursive --update --format json`;
    
    const { stdout, stderr } = await execAsync(cmd, {
      maxBuffer: 1024 * 1024 * 10, // 10MB buffer
      env: { ...process.env, PYTHONPATH: '/home/ogura/.rag/src' }
    });
    
    if (stderr) {
      console.error('Sync stderr:', stderr);
    }
    
    // 結果をパース
    try {
      const cliResult = JSON.parse(stdout);
      result.added = cliResult.indexed || 0;
      result.updated = cliResult.updated || 0;
      
      if (cliResult.error) {
        result.errors.push(cliResult.error.message);
      }
    } catch (parseError) {
      console.log('Sync output:', stdout);
    }
    
  } catch (error) {
    result.errors.push(error.message);
  }
  
  result.time_taken_ms = Date.now() - startTime;
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
    const text = result.text || '';
    
    // カテゴリフィルタ（テキスト内を検索）
    if (filters.category) {
      // メタデータにcategoryがある場合はそれを使用
      if (metadata.category) {
        if (metadata.category !== filters.category) {
          return false;
        }
      } else {
        // テキスト内に「カテゴリ: xxx」の形式があるか検索
        const categoryMatch = text.match(/カテゴリ[：:]\s*([^\n]+)/);
        if (!categoryMatch || !categoryMatch[1].includes(filters.category)) {
          return false;
        }
      }
    }
    
    // タグフィルタ（テキスト内を検索）
    if (filters.tags && filters.tags.length > 0) {
      // メタデータにtagsがある場合はそれを使用
      if (metadata.tags && metadata.tags.length > 0) {
        const hasMatchingTag = filters.tags.some(tag => metadata.tags.includes(tag));
        if (!hasMatchingTag) {
          return false;
        }
      } else {
        // テキスト内に「タグ: #xxx」の形式があるか検索
        const tagMatch = text.match(/タグ[：:]\s*([^\n]+)/);
        if (tagMatch) {
          const textTags = tagMatch[1].match(/#\w+/g) || [];
          const hasMatchingTag = filters.tags.some(filterTag => 
            textTags.some(textTag => textTag.includes(filterTag) || filterTag.includes(textTag.replace('#', '')))
          );
          if (!hasMatchingTag) {
            return false;
          }
        } else {
          return false;
        }
      }
    }
    
    // プロジェクトフィルタ（実際に存在するフィールド）
    if (filters.project_id && metadata.project_id !== filters.project_id) {
      return false;
    }
    
    // ファイルタイプフィルタ
    if (filters.file_type && metadata.file_type !== filters.file_type) {
      return false;
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
  if (!results || results.length === 0) {
    return results;
  }
  
  const queryTerms = query.toLowerCase().split(/\s+/);
  
  return results.map(result => {
    const text = result.text || '';
    const lowerText = text.toLowerCase();
    
    // 各クエリ語の位置を検索
    const positions = [];
    queryTerms.forEach(term => {
      let index = lowerText.indexOf(term);
      while (index !== -1) {
        positions.push({
          start: index,
          end: index + term.length,
          term: term
        });
        index = lowerText.indexOf(term, index + 1);
      }
    });
    
    // 位置情報を追加
    if (positions.length > 0) {
      result.match_positions = positions;
      
      // ハイライト用のプレビューを作成（最初のマッチ周辺）
      const firstMatch = positions[0];
      const contextStart = Math.max(0, firstMatch.start - 50);
      const contextEnd = Math.min(text.length, firstMatch.end + 50);
      
      result.highlighted_preview = text.substring(contextStart, contextEnd);
    }
    
    return result;
  });
}

/**
 * ヘルパー関数: 再帰的にファイルを取得
 */
function getAllFiles(dirPath, extensions, files = []) {
  const items = fs.readdirSync(dirPath);
  
  for (const item of items) {
    const fullPath = path.join(dirPath, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory()) {
      // ディレクトリの場合は再帰
      getAllFiles(fullPath, extensions, files);
    } else if (extensions.some(ext => item.endsWith(ext))) {
      // 指定された拡張子のファイルを追加
      files.push(fullPath);
    }
  }
  
  return files;
}