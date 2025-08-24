#!/usr/bin/env node

/**
 * RAG Second Brain - MCP Server
 * Node.js implementation for Model Context Protocol integration
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

const execAsync = promisify(exec);

// RAGコマンドのパス設定
const RAG_HOME = process.env.RAG_HOME || path.join(os.homedir(), '.rag');
const RAG_CMD = path.join(RAG_HOME, 'venv', 'bin', 'rag');

// MCPサーバー初期化
const server = new Server({
  name: "rag-second-brain",
  version: "1.0.0",
}, {
  capabilities: {
    tools: {},
    resources: {},
    prompts: {}
  }
});

// ツール一覧の定義
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "rag_search",
      description: "RAGシステムでドキュメントを検索",
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
            default: "vector",
            description: "検索タイプ"
          },
          top_k: {
            type: "number",
            default: 5,
            description: "検索結果数"
          }
        },
        required: ["query"]
      }
    },
    {
      name: "rag_index",
      description: "ドキュメントをインデックスに追加",
      inputSchema: {
        type: "object",
        properties: {
          path: {
            type: "string",
            description: "インデックス対象のパス"
          },
          project_id: {
            type: "string",
            description: "プロジェクトID"
          },
          recursive: {
            type: "boolean",
            default: false,
            description: "再帰的にインデックス"
          }
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
          project_id: {
            type: "string",
            description: "プロジェクトID（省略可）"
          }
        }
      }
    },
    {
      name: "rag_projects",
      description: "プロジェクト一覧を取得",
      inputSchema: {
        type: "object",
        properties: {}
      }
    },
    {
      name: "rag_documents",
      description: "ドキュメント一覧を取得",
      inputSchema: {
        type: "object",
        properties: {
          project_id: {
            type: "string",
            description: "プロジェクトID"
          },
          limit: {
            type: "number",
            default: 10,
            description: "表示件数"
          }
        }
      }
    }
  ]
}));

// ツールの実行
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    let cmd = '';
    
    switch (name) {
      case "rag_search": {
        const { query, project_id, search_type = "vector", top_k = 5 } = args;
        cmd = `${RAG_CMD} search "${query}"`;
        if (project_id) cmd += ` --project ${project_id}`;
        cmd += ` --type ${search_type}`;
        cmd += ` --top-k ${top_k}`;
        cmd += ` --output-format json`;
        break;
      }
      
      case "rag_index": {
        const { path: indexPath, project_id, recursive = false } = args;
        cmd = `${RAG_CMD} index "${indexPath}" --project ${project_id}`;
        if (recursive) cmd += ` --recursive`;
        break;
      }
      
      case "rag_stats": {
        const { project_id } = args;
        cmd = `${RAG_CMD} stats`;
        if (project_id) cmd += ` --project ${project_id}`;
        cmd += ` --output-format json`;
        break;
      }
      
      case "rag_projects": {
        cmd = `${RAG_CMD} projects --output-format json`;
        break;
      }
      
      case "rag_documents": {
        const { project_id, limit = 10 } = args;
        cmd = `${RAG_CMD} documents`;
        if (project_id) cmd += ` --project ${project_id}`;
        cmd += ` | head -${limit}`;
        break;
      }
      
      default:
        return {
          content: [{
            type: "text",
            text: `Unknown tool: ${name}`
          }]
        };
    }
    
    console.error(`Executing: ${cmd}`);
    const { stdout, stderr } = await execAsync(cmd, {
      env: { ...process.env, PYTHONPATH: path.join(RAG_HOME, 'src') }
    });
    
    if (stderr && !stderr.includes('INFO:') && !stderr.includes('WARNING:')) {
      console.error(`stderr: ${stderr}`);
    }
    
    return {
      content: [{
        type: "text",
        text: stdout || "Command executed successfully"
      }]
    };
    
  } catch (error) {
    console.error(`Error executing ${name}:`, error);
    return {
      content: [{
        type: "text",
        text: `Error: ${error.message}`
      }]
    };
  }
});

// リソース一覧の定義
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [
    {
      uri: "rag://stats",
      name: "RAG Statistics",
      description: "RAGシステムの統計情報",
      mimeType: "application/json"
    },
    {
      uri: "rag://projects",
      name: "Projects List",
      description: "プロジェクト一覧",
      mimeType: "application/json"
    }
  ]
}));

// リソースの読み取り
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;
  
  try {
    let cmd = '';
    
    switch (uri) {
      case "rag://stats":
        cmd = `${RAG_CMD} stats --output-format json`;
        break;
      case "rag://projects":
        cmd = `${RAG_CMD} projects --output-format json`;
        break;
      default:
        return {
          contents: [{
            uri,
            mimeType: "text/plain",
            text: "Unknown resource"
          }]
        };
    }
    
    const { stdout } = await execAsync(cmd, {
      env: { ...process.env, PYTHONPATH: path.join(RAG_HOME, 'src') }
    });
    
    return {
      contents: [{
        uri,
        mimeType: "application/json",
        text: stdout
      }]
    };
  } catch (error) {
    return {
      contents: [{
        uri,
        mimeType: "text/plain",
        text: `Error: ${error.message}`
      }]
    };
  }
});

// プロンプト一覧
server.setRequestHandler(ListPromptsRequestSchema, async () => ({
  prompts: [
    {
      name: "search_docs",
      description: "ドキュメント検索用プロンプト",
      arguments: [
        {
          name: "topic",
          description: "検索トピック",
          required: true
        }
      ]
    }
  ]
}));

// プロンプトの取得
server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  if (name === "search_docs") {
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `以下のトピックについて、RAGシステムで検索してください: ${args.topic}`
          }
        }
      ]
    };
  }
  
  return { messages: [] };
});

// サーバー起動
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("RAG Second Brain MCP Server started");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});