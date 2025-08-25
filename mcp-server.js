#!/usr/bin/env node

/**
 * RAG Second Brain - Enhanced MCP Server with Fallback Search
 * Phase 1 フォールバック機能統合版
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { 
  ListToolsRequestSchema, 
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema
} from "@modelcontextprotocol/sdk/types.js";
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import os from 'os';
import fs from 'fs';
import {
  executeRagIndex,
  executeRagDelete,
  executeRagSync,
  applyFilters,
  addPositionAndHighlights
} from './mcp-tools-implementation.js';

const execAsync = promisify(exec);

// RAGコマンドのパス設定（先に定義）
const RAG_HOME = process.env.RAG_HOME || path.join(os.homedir(), '.rag');
const RAG_CMD = path.join(RAG_HOME, 'venv', 'bin', 'rag');

// PIDファイルのパス
const PID_FILE = path.join(RAG_HOME, 'mcp-server.pid');

// 起動時に古いプロセスを終了
async function killOldProcesses() {
  try {
    // 現在のプロセスIDを取得
    const currentPid = process.pid;
    
    // PIDファイルから前回のプロセスIDを読み取る
    if (fs.existsSync(PID_FILE)) {
      try {
        const oldPid = fs.readFileSync(PID_FILE, 'utf8').trim();
        if (oldPid && oldPid !== String(currentPid)) {
          // プロセスが存在するか確認
          try {
            await execAsync(`ps -p ${oldPid}`);
            // プロセスが存在する場合は終了
            await execAsync(`kill ${oldPid}`);
            console.error(`✅ 古いMCPプロセス (PID: ${oldPid}) を終了しました`);
          } catch (e) {
            // プロセスが存在しない場合は何もしない
          }
        }
      } catch (e) {
        console.error('PIDファイルの読み取りエラー:', e.message);
      }
    }
    
    // 追加の安全対策：同じmcp-server.jsを実行している他のプロセスも検索
    const { stdout } = await execAsync(
      `ps aux | grep "rag-second-brain/mcp-server.js" | grep -v grep | awk '{print $2}'`
    );
    
    const pids = stdout.trim().split('\n').filter(pid => pid && pid !== String(currentPid));
    
    if (pids.length > 0) {
      console.error(`🔄 残っている古いMCPプロセスを終了中: ${pids.join(', ')}`);
      for (const pid of pids) {
        try {
          await execAsync(`kill ${pid}`);
          console.error(`  ✅ PID ${pid} を終了しました`);
        } catch (e) {
          // プロセスが既に終了している場合はエラーを無視
        }
      }
    }
    
    // 現在のPIDをファイルに保存
    fs.writeFileSync(PID_FILE, String(currentPid));
    console.error(`📝 現在のPID (${currentPid}) を保存しました`);
    
  } catch (error) {
    // エラーが発生しても処理を継続
    console.error('古いプロセスの終了中にエラー:', error.message);
  }
}

// 起動時に古いプロセスを終了
await killOldProcesses();

// プロセス終了時のクリーンアップ
process.on('exit', () => {
  try {
    if (fs.existsSync(PID_FILE)) {
      const savedPid = fs.readFileSync(PID_FILE, 'utf8').trim();
      if (savedPid === String(process.pid)) {
        fs.unlinkSync(PID_FILE);
        console.error('📝 PIDファイルを削除しました');
      }
    }
  } catch (e) {
    // エラーを無視
  }
});

process.on('SIGINT', () => {
  console.error('🛑 MCPサーバーを終了中...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.error('🛑 MCPサーバーを終了中...');
  process.exit(0);
});

// Phase 1 フォールバック機能のパス
const ULTRA_RAG_PATH = '/home/ogura/work/ultra/rag-second-brain';
const COMPOUND_TERMS_PATH = path.join(ULTRA_RAG_PATH, 'data', 'compound_terms.json');

// 複合語辞書を読み込み
let compoundTerms = {};
try {
  const data = fs.readFileSync(COMPOUND_TERMS_PATH, 'utf8');
  compoundTerms = JSON.parse(data).compound_terms;
  console.error(`複合語辞書読み込み完了: ${Object.keys(compoundTerms).length}件`);
} catch (error) {
  console.error('複合語辞書の読み込みに失敗:', error.message);
}

/**
 * クエリ前処理関数 - Phase 1 フォールバック機能
 */
function preprocessQuery(query) {
  const variations = [query]; // 元のクエリは必ず含める
  
  // 複合語の処理
  if (compoundTerms[query]) {
    const termData = compoundTerms[query];
    
    // スペース区切り版を追加
    if (termData.tokens && termData.tokens.length > 1) {
      variations.push(termData.tokens.join(' '));
    }
    
    // 同義語を追加
    if (termData.synonyms) {
      variations.push(...termData.synonyms);
    }
  }
  
  // 一般的な前処理
  if (query.match(/[a-zA-Z]+[ひ-ゞ]+/)) {
    // 英語+日本語の場合、スペース区切りを試す
    const spaced = query.replace(/([a-zA-Z]+)([ひ-ゞ]+)/g, '$1 $2');
    variations.push(spaced);
  }
  
  return [...new Set(variations)]; // 重複除去
}

/**
 * クエリ分割関数
 */
function splitQuery(query) {
  // 複合語の場合、トークンに分割
  if (compoundTerms[query] && compoundTerms[query].tokens) {
    return compoundTerms[query].tokens;
  }
  
  // 英語・日本語の境界で分割
  const parts = query.split(/(?=[A-Z])|(?<=[a-z])(?=[あ-ん])|(?<=[あ-ん])(?=[A-Za-z])/);
  return parts.filter(p => p.length > 0);
}

/**
 * フォールバック検索実行
 */
async function executeWithFallback(query, searchType = 'hybrid', topK = 5, projectId = null) {
  const results = [];
  const searchHistory = [];
  
  // Step 1: 直接検索
  try {
    console.error(`🔍 Step 1: 直接検索 '${query}'`);
    const directResult = await executeRagSearch(query, searchType, topK, projectId);
    
    if (directResult.success && directResult.count > 0) {
      results.push({
        method: 'direct',
        query: query,
        result: directResult,
        weight: 1.0
      });
      searchHistory.push(`✅ 直接検索成功: ${directResult.count}件取得`);
      
      // 十分な結果があれば完了
      if (directResult.count >= 1) {
        return formatFallbackResult(results, searchHistory, query);
      }
    } else {
      searchHistory.push(`❌ 直接検索失敗: ${directResult.error || '結果なし'}`);
    }
  } catch (error) {
    searchHistory.push(`❌ 直接検索エラー: ${error.message}`);
  }
  
  // Step 2: 前処理クエリ検索
  console.error(`🔄 Step 2: 前処理クエリ検索`);
  const preprocessedQueries = preprocessQuery(query);
  
  for (let i = 1; i < Math.min(preprocessedQueries.length, 4); i++) {
    const prepQuery = preprocessedQueries[i];
    if (prepQuery === query) continue;
    
    try {
      console.error(`   🔍 前処理クエリ${i}: '${prepQuery}'`);
      const prepResult = await executeRagSearch(prepQuery, searchType, Math.ceil(topK / 2), projectId);
      
      if (prepResult.success && prepResult.count > 0) {
        results.push({
          method: 'preprocessed',
          query: prepQuery,
          result: prepResult,
          weight: 0.8
        });
        searchHistory.push(`✅ 前処理クエリ '${prepQuery}': ${prepResult.count}件取得`);
        
        if (results.length >= 2) break; // 十分な結果が得られた
      } else {
        searchHistory.push(`❌ 前処理クエリ '${prepQuery}': ${prepResult.error || '結果なし'}`);
      }
    } catch (error) {
      searchHistory.push(`❌ 前処理クエリ '${prepQuery}': ${error.message}`);
    }
  }
  
  // Step 3: 分割クエリ検索
  if (results.length < 2) {
    console.error(`🔪 Step 3: 分割クエリ検索`);
    const splitParts = splitQuery(query);
    
    if (splitParts.length > 1) {
      for (let i = 0; i < splitParts.length && i < 2; i++) {
        const part = splitParts[i];
        
        try {
          console.error(`   🔍 分割クエリ${i + 1}: '${part}'`);
          const splitResult = await executeRagSearch(part, searchType, Math.max(1, Math.ceil(topK / splitParts.length)), projectId);
          
          if (splitResult.success && splitResult.count > 0) {
            results.push({
              method: 'split',
              query: part,
              result: splitResult,
              weight: 0.4
            });
            searchHistory.push(`✅ 分割クエリ '${part}': ${splitResult.count}件取得`);
          } else {
            searchHistory.push(`❌ 分割クエリ '${part}': ${splitResult.error || '結果なし'}`);
          }
        } catch (error) {
          searchHistory.push(`❌ 分割クエリ '${part}': ${error.message}`);
        }
      }
    }
  }
  
  return formatFallbackResult(results, searchHistory, query);
}

/**
 * Grep検索実行（改善案2: ハイブリッド検索用）
 */
async function executeGrepSearch(query, projectPath) {
  try {
    // プロジェクトのルートパスを決定
    const searchPath = projectPath || '/home/ogura/work/ultra';
    
    // grepコマンドを構築（大文字小文字を無視）
    const cmd = `grep -r -i "${query}" "${searchPath}" --include="*.md" --include="*.txt" --include="*.py" --include="*.js" --include="*.php" 2>/dev/null | head -20`;
    
    const { stdout, stderr } = await execAsync(cmd, {
      timeout: 10000 // 10秒タイムアウト
    });
    
    if (!stdout || stdout.trim() === '') {
      return {
        success: false,
        results: [],
        error: 'No grep results found'
      };
    }
    
    // grep結果をパース
    const lines = stdout.trim().split('\n').slice(0, 10); // 最大10行
    const results = lines.map((line, index) => {
      const colonIndex = line.indexOf(':');
      const filePath = colonIndex > 0 ? line.substring(0, colonIndex) : '';
      const content = colonIndex > 0 ? line.substring(colonIndex + 1).trim() : line;
      
      return {
        file_path: filePath,
        text: content.substring(0, 80) + (content.length > 80 ? '...' : ''), // 80文字に制限
        score: 0.8 - (index * 0.05), // 順位に基づくスコア
        source: 'grep'
      };
    });
    
    return {
      success: true,
      results: results,
      count: results.length
    };
  } catch (error) {
    console.error(`Grep search error: ${error.message}`);
    return {
      success: false,
      results: [],
      error: error.message
    };
  }
}

/**
 * ハイブリッド検索実行（改善案2: Grep + Vector検索）
 */
async function executeHybridSearchWithGrep(query, topK, projectId) {
  const results = [];
  
  console.error(`🔍 ハイブリッド検索開始: Grep + Vector for "${query}"`);
  
  // 1. Grep検索を実行
  const grepResult = await executeGrepSearch(query);
  if (grepResult.success && grepResult.results.length > 0) {
    console.error(`✅ Grep検索: ${grepResult.results.length}件`);
    results.push({
      method: 'grep',
      results: grepResult.results,
      weight: 0.4 // Grepの重み
    });
  }
  
  // 2. Vector検索を実行
  const vectorResult = await executeRagSearch(query, 'vector', topK, projectId);
  if (vectorResult.success && vectorResult.data && vectorResult.data.results) {
    console.error(`✅ Vector検索: ${vectorResult.data.results.length}件`);
    results.push({
      method: 'vector',
      results: vectorResult.data.results,
      weight: 0.6 // Vectorの重み
    });
  }
  
  // 結果をマージしてフォーマット
  const mergedResults = [];
  const seenFiles = new Set();
  
  // 両方の結果を統合
  for (const searchResult of results) {
    for (const item of searchResult.results) {
      const fileKey = item.file_path || item.metadata?.file_path || '';
      
      // 重複を避ける
      if (fileKey && seenFiles.has(fileKey)) {
        continue;
      }
      if (fileKey) seenFiles.add(fileKey);
      
      mergedResults.push({
        ...item,
        search_method: searchResult.method,
        combined_score: (item.score || 0.5) * searchResult.weight
      });
    }
  }
  
  // スコアでソート
  mergedResults.sort((a, b) => b.combined_score - a.combined_score);
  
  return {
    query: query,
    search_type: 'hybrid_grep_vector',
    total_found: mergedResults.length,
    results: mergedResults.slice(0, topK)
  };
}

/**
 * RAG検索実行（単一クエリ）
 */
async function executeRagSearch(query, searchType, topK, projectId) {
  try {
    let cmd = `${RAG_CMD} search "${query}"`;
    if (projectId) cmd += ` --project ${projectId}`;
    cmd += ` --type ${searchType}`;
    cmd += ` --top-k ${topK}`;
    cmd += ` --format json`;
    
    // デバッグログ追加
    console.error(`[DEBUG] Executing command: ${cmd}`);
    console.error(`[DEBUG] RAG_CMD: ${RAG_CMD}`);
    console.error(`[DEBUG] RAG_HOME: ${RAG_HOME}`);
    console.error(`[DEBUG] Working directory: ${process.cwd()}`);
    
    const { stdout, stderr } = await execAsync(cmd, {
      env: { 
        ...process.env, 
        PYTHONPATH: path.join(RAG_HOME, 'src'),
        RAG_HOME: RAG_HOME,
        HOME: os.homedir()
      },
      cwd: RAG_HOME,  // 作業ディレクトリを明示的に設定
      timeout: 30000 // 30秒タイムアウト
    });
    
    // デバッグ: 標準エラー出力
    if (stderr) {
      console.error(`[DEBUG] stderr: ${stderr}`);
    }
    
    // デバッグ: 標準出力の最初の500文字
    console.error(`[DEBUG] stdout (first 500 chars): ${stdout.substring(0, 500)}`);
    
    // JSON結果をパース - 最後の{で始まる行を探す（それがJSON出力）
    const lines = stdout.trim().split('\n');
    let jsonResult = null;
    
    // 後ろから探して最初のJSONを見つける
    for (let i = lines.length - 1; i >= 0; i--) {
      const line = lines[i];
      if (line.trim().startsWith('{')) {
        try {
          jsonResult = JSON.parse(line);
          console.error(`[DEBUG] JSON parsed successfully: ${jsonResult.results ? jsonResult.results.length : 0} results`);
          break;
        } catch (e) {
          console.error(`[DEBUG] JSON parse error on line ${i}: ${e.message}`);
          console.error(`[DEBUG] Attempted to parse: ${line.substring(0, 100)}...`);
        }
      }
    }
    
    if (jsonResult && jsonResult.results) {
      // トークン制限対策: 各結果のテキストを80文字に制限
      const truncatedResults = jsonResult.results.map(result => {
        const truncatedResult = { ...result };
        
        // textフィールドを80文字に制限
        if (truncatedResult.text && truncatedResult.text.length > 80) {
          truncatedResult.text = truncatedResult.text.substring(0, 80) + '...';
        }
        
        // documentフィールドも80文字に制限
        if (truncatedResult.document && truncatedResult.document.length > 80) {
          truncatedResult.document = truncatedResult.document.substring(0, 80) + '...';
        }
        
        // metadataの不要なフィールドを削除
        if (truncatedResult.metadata) {
          const minimalMetadata = {
            file_path: truncatedResult.metadata.file_path,
            project_id: truncatedResult.metadata.project_id
          };
          // カテゴリとタグは残す（フィルタリング用）
          if (truncatedResult.metadata.category) {
            minimalMetadata.category = truncatedResult.metadata.category;
          }
          if (truncatedResult.metadata.tags) {
            minimalMetadata.tags = truncatedResult.metadata.tags;
          }
          truncatedResult.metadata = minimalMetadata;
        }
        
        return truncatedResult;
      });
      
      return {
        success: true,
        count: truncatedResults.length,
        data: { ...jsonResult, results: truncatedResults },
        error: null
      };
    } else {
      // テキスト形式の結果をカウント
      const foundLine = lines.find(line => line.includes('Found') && line.includes('results'));
      const count = foundLine ? parseInt(foundLine.match(/(\d+)/)?.[1] || '0') : 0;
      
      return {
        success: count > 0,
        count: count,
        data: { results: [], raw_output: stdout },
        error: count === 0 ? 'No results found' : null
      };
    }
  } catch (error) {
    console.error(`[DEBUG] executeRagSearch error: ${error.message}`);
    console.error(`[DEBUG] error stack: ${error.stack}`);
    return {
      success: false,
      count: 0,
      data: null,
      error: error.message
    };
  }
}

/**
 * フォールバック結果のフォーマット
 */
function formatFallbackResult(results, searchHistory, originalQuery) {
  const output = {
    query: originalQuery,
    search_type: 'fallback_enhanced',
    total_methods: results.length,
    search_history: searchHistory,
    results: []
  };
  
  // 結果をスコア順にマージ
  const allResults = [];
  for (const result of results) {
    if (result.result.data && result.result.data.results) {
      for (const item of result.result.data.results) {
        // すでにexecuteRagSearchで80文字に制限済みなので、追加の処理は不要
        const trimmedItem = {
          ...item,
          search_method: result.method,
          search_query: result.query.substring(0, 30),  // 検索クエリも30文字に制限
          weighted_score: (item.score || 0.5) * result.weight
        };
        
        allResults.push(trimmedItem);
      }
    }
  }
  
  // 重み付きスコアでソート
  allResults.sort((a, b) => b.weighted_score - a.weighted_score);
  output.results = allResults.slice(0, 5); // 上位5件
  output.total_found = allResults.length;
  
  return output;
}

// MCPサーバー初期化
const server = new Server({
  name: "rag-second-brain-enhanced",
  version: "1.1.0",
}, {
  capabilities: {
    tools: {},
    resources: {},
    prompts: {}
  }
});

// ツール一覧の定義（フォールバック機能付き）
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "rag_search",
      description: "RAGシステムでドキュメントを検索（Phase 1 フォールバック機能付き）",
      inputSchema: {
        type: "object",
        properties: {
          query: { 
            type: "string",
            description: "検索クエリ"
          },
          project_id: { 
            type: "string",
            description: "プロジェクトID（省略可）"
          },
          search_type: {
            type: "string",
            enum: ["vector", "keyword", "hybrid", "hybrid_grep"],
            default: "hybrid",
            description: "検索タイプ（hybrid_grep: Grep+Vector検索）"
          },
          top_k: {
            type: "number",
            default: 5,
            description: "検索結果数"
          },
          use_fallback: {
            type: "boolean",
            default: true,
            description: "フォールバック機能を使用"
          },
          filters: {
            type: "object",
            description: "検索結果のフィルタ条件",
            properties: {
              category: { type: "string", description: "カテゴリでフィルタ" },
              tags: { type: "array", items: { type: "string" }, description: "タグでフィルタ" },
              created_after: { type: "string", description: "作成日時の開始" },
              created_before: { type: "string", description: "作成日時の終了" }
            }
          }
        },
        required: ["query"]
      }
    },
    // 他のツールは元のまま...
    {
      name: "rag_index",
      description: "ドキュメントをインデックスに追加",
      inputSchema: {
        type: "object",
        properties: {
          path: { type: "string", description: "インデックス対象のパス" },
          project_id: { type: "string", description: "プロジェクトID" },
          recursive: { type: "boolean", default: false, description: "再帰的にインデックス" },
          metadata: { type: "object", description: "追加メタデータ" },
          update: { type: "boolean", default: false, description: "既存ドキュメントを更新" }
        },
        required: ["path", "project_id"]
      }
    },
    {
      name: "rag_delete",
      description: "ドキュメントを削除",
      inputSchema: {
        type: "object",
        properties: {
          document_id: { type: "string", description: "削除するドキュメントID" },
          project: { type: "string", description: "削除するプロジェクトID" },
          filters: {
            type: "object",
            description: "削除条件",
            properties: {
              older_than: { type: "string", description: "指定日数より古い" },
              category: { type: "string", description: "カテゴリ" },
              source_type: { type: "string", description: "ソースタイプ" }
            }
          }
        }
      }
    },
    {
      name: "rag_sync",
      description: "プロジェクトのドキュメントを同期",
      inputSchema: {
        type: "object",
        properties: {
          project: { type: "string", description: "プロジェクトID" },
          path: { type: "string", description: "同期対象のパス" },
          full: { type: "boolean", default: false, description: "完全再インデックス" },
          remove_deleted: { type: "boolean", default: true, description: "削除ファイルを反映" }
        },
        required: ["project", "path"]
      }
    },
    {
      name: "rag_stats",
      description: "RAGシステムの統計情報を取得",
      inputSchema: {
        type: "object",
        properties: {
          project_id: { type: "string", description: "プロジェクトID（省略可）" }
        }
      }
    },
    {
      name: "rag_projects",
      description: "プロジェクト一覧を取得",
      inputSchema: { type: "object", properties: {} }
    },
    {
      name: "rag_documents",
      description: "ドキュメント一覧を取得",
      inputSchema: {
        type: "object",
        properties: {
          project_id: { type: "string", description: "プロジェクトID" },
          limit: { type: "number", default: 10, description: "表示件数" }
        }
      }
    }
  ]
}));

// ツールの実行（フォールバック機能統合版）
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    switch (name) {
      case "rag_search": {
        const { query, project_id, search_type = "hybrid", top_k = 5, use_fallback = true, filters } = args;
        
        // 改善案2: hybrid_grepタイプの処理
        if (search_type === "hybrid_grep") {
          console.error(`🔀 ハイブリッド検索（Grep + Vector）を実行`);
          const result = await executeHybridSearchWithGrep(query, top_k, project_id);
          
          return {
            content: [{
              type: "text",
              text: JSON.stringify(result, null, 2)
            }]
          };
        }
        
        if (use_fallback) {
          // Phase 1 フォールバック検索を実行
          let result = await executeWithFallback(query, search_type, top_k, project_id);
          
          // デバッグログ
          console.error(`[DEBUG] executeWithFallback result count:`, result.results ? result.results.length : 0);
          
          try {
            // フィルタリング適用
            if (filters && Object.keys(filters).length > 0 && result.results) {
              const { applyFilters } = await import('./mcp-tools-implementation.js');
              result.results = applyFilters(result.results, filters);
              console.error(`[DEBUG] After filtering: ${result.results.length} results`);
            }
            
            // 位置情報とハイライトの追加
            if (result.results && result.results.length > 0) {
              const { addPositionAndHighlights } = await import('./mcp-tools-implementation.js');
              result.results = addPositionAndHighlights(result.results, query);
              console.error(`[DEBUG] After highlights: ${result.results.length} results`);
            }
          } catch (error) {
            console.error(`[ERROR] Filter/Highlight processing failed:`, error.message);
            // エラーが発生してもオリジナルの結果を返す
          }
          
          return {
            content: [{
              type: "text",
              text: JSON.stringify(result, null, 2)
            }]
          };
        } else {
          // 通常の検索を実行
          const searchResult = await executeRagSearch(query, search_type, top_k, project_id);
          
          // 結果をフォーマット（トークン制限対策済み）
          const formattedResult = {
            success: searchResult.success,
            query: query.substring(0, 50),  // クエリも50文字に制限
            search_type: search_type,
            count: searchResult.count,
            results: searchResult.data ? searchResult.data.results : []
          };
          
          // フィルタリング適用
          if (filters && Object.keys(filters).length > 0 && formattedResult.results) {
            formattedResult.results = applyFilters(formattedResult.results, filters);
            formattedResult.count = formattedResult.results.length;
          }
          
          return {
            content: [{
              type: "text",
              text: JSON.stringify(formattedResult, null, 2)
            }]
          };
        }
      }
      
      // rag_index Tool - ドキュメントのインデックス作成
      case "rag_index": {
        const { path: indexPath, project_id, recursive = false, metadata, update } = args;
        
        if (!indexPath || !project_id) {
          return {
            content: [{
              type: "text",
              text: JSON.stringify({
                error: "Missing required parameters: path and project_id"
              })
            }]
          };
        }
        
        const result = await executeRagIndex(indexPath, project_id, {
          recursive,
          metadata,
          update
        });
        
        return {
          content: [{
            type: "text",
            text: JSON.stringify(result, null, 2)
          }]
        };
      }
      
      // rag_delete Tool - ドキュメントの削除
      case "rag_delete": {
        const { document_id, project, filters } = args;
        
        if (!document_id && !project && !filters) {
          return {
            content: [{
              type: "text",
              text: JSON.stringify({
                error: "At least one parameter required: document_id, project, or filters"
              })
            }]
          };
        }
        
        const result = await executeRagDelete({
          document_id,
          project,
          filters
        });
        
        return {
          content: [{
              type: "text",
              text: JSON.stringify(result, null, 2)
          }]
        };
      }
      
      // rag_sync Tool - プロジェクトの同期
      case "rag_sync": {
        const { project, path: syncPath, full = false, remove_deleted = true } = args;
        
        if (!project || !syncPath) {
          return {
            content: [{
              type: "text",
              text: JSON.stringify({
                error: "Missing required parameters: project and path"
              })
            }]
          };
        }
        
        const result = await executeRagSync(project, syncPath, {
          full,
          remove_deleted
        });
        
        return {
          content: [{
            type: "text",
            text: JSON.stringify(result, null, 2)
          }]
        };
      }
      
      case "rag_stats": {
        const { project_id } = args;
        // statsコマンドは現在project_idパラメータをサポートしていない
        let cmd = `${RAG_CMD} stats`;
        
        const { stdout } = await execAsync(cmd);
        return {
          content: [{ type: "text", text: stdout }]
        };
      }
      
      case "rag_projects": {
        const cmd = `${RAG_CMD} projects`;
        const { stdout } = await execAsync(cmd);
        return {
          content: [{ type: "text", text: stdout }]
        };
      }
      
      case "rag_documents": {
        const { project_id, limit = 10 } = args;
        let cmd = `${RAG_CMD} documents`;
        if (project_id) cmd += ` --project ${project_id}`;
        cmd += ` | head -${limit}`;
        
        const { stdout } = await execAsync(cmd);
        return {
          content: [{ type: "text", text: stdout }]
        };
      }
      
      default:
        return {
          content: [{
            type: "text",
            text: `Unknown tool: ${name}`
          }]
        };
    }
  } catch (error) {
    console.error(`Tool execution error: ${error.message}`);
    return {
      content: [{
        type: "text",
        text: `Error: ${error.message}`
      }]
    };
  }
});

// リソース定義
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [
    {
      uri: "rag://fallback-status",
      name: "Phase 1 フォールバック機能状態",
      mimeType: "application/json",
      description: "フォールバック検索機能の統計情報"
    }
  ]
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;
  
  if (uri === "rag://fallback-status") {
    const status = {
      phase: "Phase 1",
      compound_terms_loaded: Object.keys(compoundTerms).length,
      features: {
        "複合語前処理": true,
        "3段階フォールバック": true,
        "重み付きランキング": true,
        "MCP統合": true
      },
      sample_terms: Object.keys(compoundTerms).slice(0, 5)
    };
    
    return {
      contents: [{
        uri: uri,
        mimeType: "application/json",
        text: JSON.stringify(status, null, 2)
      }]
    };
  }
  
  throw new Error(`Resource not found: ${uri}`);
});

// サーバー起動
const transport = new StdioServerTransport();
server.connect(transport);

console.error("RAG Second Brain Enhanced MCP Server with Phase 1 Fallback started");
console.error(`複合語辞書: ${Object.keys(compoundTerms).length}件読み込み済み`);
console.error("フォールバック機能: 有効");