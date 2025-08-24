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

const execAsync = promisify(exec);

// RAGコマンドのパス設定
const RAG_HOME = process.env.RAG_HOME || path.join(os.homedir(), '.rag');
const RAG_CMD = path.join(RAG_HOME, 'venv', 'bin', 'rag');

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
 * RAG検索実行（単一クエリ）
 */
async function executeRagSearch(query, searchType, topK, projectId) {
  try {
    let cmd = `${RAG_CMD} search "${query}"`;
    if (projectId) cmd += ` --project ${projectId}`;
    cmd += ` --type ${searchType}`;
    cmd += ` --top-k ${topK}`;
    cmd += ` --format json`;
    
    const { stdout, stderr } = await execAsync(cmd, {
      env: { ...process.env, PYTHONPATH: path.join(RAG_HOME, 'src') },
      timeout: 30000 // 30秒タイムアウト
    });
    
    // JSON結果をパース
    const lines = stdout.trim().split('\n');
    let jsonResult = null;
    
    for (const line of lines) {
      if (line.startsWith('{')) {
        try {
          jsonResult = JSON.parse(line);
          break;
        } catch (e) {
          continue;
        }
      }
    }
    
    if (jsonResult && jsonResult.results) {
      return {
        success: true,
        count: jsonResult.results.length,
        data: jsonResult,
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
        allResults.push({
          ...item,
          search_method: result.method,
          search_query: result.query,
          weighted_score: (item.score || 0.5) * result.weight
        });
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
            enum: ["vector", "keyword", "hybrid"],
            default: "hybrid",
            description: "検索タイプ"
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
          recursive: { type: "boolean", default: false, description: "再帰的にインデックス" }
        },
        required: ["path", "project_id"]
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
        const { query, project_id, search_type = "hybrid", top_k = 5, use_fallback = true } = args;
        
        if (use_fallback) {
          // Phase 1 フォールバック検索を実行
          const result = await executeWithFallback(query, search_type, top_k, project_id);
          
          return {
            content: [{
              type: "text",
              text: JSON.stringify(result, null, 2)
            }]
          };
        } else {
          // 通常の検索を実行
          const cmd = `${RAG_CMD} search "${query}" --type ${search_type} --top-k ${top_k} --format json${project_id ? ` --project ${project_id}` : ''}`;
          console.error(`Executing: ${cmd}`);
          
          const { stdout, stderr } = await execAsync(cmd, {
            env: { ...process.env, PYTHONPATH: path.join(RAG_HOME, 'src') }
          });
          
          return {
            content: [{
              type: "text",
              text: stdout
            }]
          };
        }
      }
      
      // 他のツールの処理は元のMCPサーバーと同じ
      case "rag_index": {
        const { path: indexPath, project_id, recursive = false } = args;
        let cmd = `${RAG_CMD} index "${indexPath}" --project ${project_id}`;
        if (recursive) cmd += ` --recursive`;
        
        console.error(`Executing: ${cmd}`);
        const { stdout } = await execAsync(cmd);
        
        return {
          content: [{ type: "text", text: stdout }]
        };
      }
      
      case "rag_stats": {
        const { project_id } = args;
        let cmd = `${RAG_CMD} stats`;
        if (project_id) cmd += ` --project ${project_id}`;
        
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