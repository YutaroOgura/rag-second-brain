"""MCP Server implementation for RAG system."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    # MCP server imports - these might not be installed yet
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource, 
        Tool, 
        TextContent, 
        ImageContent, 
        EmbeddedResource,
        Prompt
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Create dummy classes for development
    class Server:
        def __init__(self, name: str): self.name = name
        def list_resources(self): pass
        def list_tools(self): pass
        def list_prompts(self): pass
        def read_resource(self, uri: str): pass
        def call_tool(self, name: str, arguments: dict): pass
        def get_prompt(self, name: str, arguments: dict): pass

from ..core.database import DatabaseManager
from ..core.vectorizer import Vectorizer
from ..core.search import SearchEngine
from ..utils.document_loader import DocumentLoader
from ..utils.config import load_config

logger = logging.getLogger(__name__)


class RAGMCPServer:
    """MCP Server for RAG system functionality."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize MCP server.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self.config = None
        self.database = None
        self.vectorizer = None
        self.search_engine = None
        self.document_loader = None
        
        # Initialize MCP server
        if MCP_AVAILABLE:
            self.server = Server("rag-second-brain")
        else:
            self.server = None
            logger.warning("MCP not available - running in compatibility mode")
    
    async def initialize(self):
        """Initialize all components."""
        try:
            # Load configuration
            self.config = load_config(self.config_path)
            logger.info("Configuration loaded")
            
            # Initialize components
            await self._init_components()
            
            # Register MCP handlers if available
            if MCP_AVAILABLE and self.server:
                self._register_handlers()
            
            logger.info("RAG MCP Server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG MCP Server: {e}")
            raise
    
    async def _init_components(self):
        """Initialize RAG system components."""
        # Database
        db_config = self.config.get('database', {})
        self.database = DatabaseManager(db_config.get('path', './data/chroma'))
        self.database.create_collection(db_config.get('collection_name', 'documents'))
        
        # Vectorizer
        emb_config = self.config.get('embedding', {})
        self.vectorizer = Vectorizer(
            model_name=emb_config.get('model', 'sentence-transformers/multilingual-e5-base'),
            device=emb_config.get('device', 'cpu')
        )
        
        # Search Engine
        self.search_engine = SearchEngine(self.database, self.vectorizer)
        
        # Document Loader
        self.document_loader = DocumentLoader()
        
        logger.info("RAG components initialized")
        
        return self.database, self.vectorizer, self.search_engine
    
    def _register_handlers(self):
        """Register MCP server handlers."""
        if not MCP_AVAILABLE or not self.server:
            return
        
        # Resources
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            return [
                Resource(
                    uri="rag://projects",
                    name="Projects",
                    mimeType="application/json",
                    description="List of all projects in the RAG system"
                ),
                Resource(
                    uri="rag://search-results",
                    name="Search Results",
                    mimeType="application/json", 
                    description="Recent search results cache"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            if uri == "rag://projects":
                projects = self.database.list_projects()
                return json.dumps(projects, ensure_ascii=False, indent=2)
            elif uri == "rag://search-results":
                # Return cached search results or empty
                return json.dumps({"results": [], "message": "No recent searches"})
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
        
        # Tools
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="rag_search",
                    description="Search documents in the RAG system using vector, keyword, or hybrid search",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query text"
                            },
                            "search_type": {
                                "type": "string",
                                "enum": ["vector", "keyword", "hybrid"],
                                "default": "vector",
                                "description": "Type of search to perform"
                            },
                            "project_id": {
                                "type": "string",
                                "description": "Optional project ID to filter results"
                            },
                            "top_k": {
                                "type": "integer",
                                "default": 5,
                                "description": "Number of results to return"
                            },
                            "alpha": {
                                "type": "number",
                                "default": 0.5,
                                "description": "Alpha value for hybrid search (0.0=vector, 1.0=keyword)"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="rag_index",
                    description="Index documents from file or directory into the RAG system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to file or directory to index"
                            },
                            "project_id": {
                                "type": "string",
                                "description": "Project ID for the documents"
                            },
                            "recursive": {
                                "type": "boolean",
                                "default": False,
                                "description": "Process directory recursively"
                            }
                        },
                        "required": ["path", "project_id"]
                    }
                ),
                Tool(
                    name="rag_suggest",
                    description="Get query suggestions based on existing documents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Base query for suggestions"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 5,
                                "description": "Number of suggestions to return"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="rag_stats",
                    description="Get statistics about the RAG system",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            try:
                if name == "rag_search":
                    return await self.rag_search(**arguments)
                elif name == "rag_index":
                    return await self.rag_index(**arguments)
                elif name == "rag_suggest":
                    return await self.rag_suggest(**arguments)
                elif name == "rag_stats":
                    return await self.rag_stats(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Tool {name} failed: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Prompts
        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            return [
                Prompt(
                    name="search_context",
                    description="Generate context from search results for LLM consumption",
                    arguments=[
                        {
                            "name": "query",
                            "description": "Search query",
                            "required": True
                        },
                        {
                            "name": "max_results",
                            "description": "Maximum results to include",
                            "required": False
                        }
                    ]
                ),
                Prompt(
                    name="code_documentation",
                    description="Generate documentation context for code-related queries",
                    arguments=[
                        {
                            "name": "topic",
                            "description": "Documentation topic",
                            "required": True
                        },
                        {
                            "name": "project_id",
                            "description": "Project to focus on",
                            "required": False
                        }
                    ]
                )
            ]
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: dict) -> str:
            if name == "search_context":
                return await self._generate_search_context_prompt(**arguments)
            elif name == "code_documentation":
                return await self._generate_documentation_prompt(**arguments)
            else:
                raise ValueError(f"Unknown prompt: {name}")
    
    async def rag_search(
        self,
        query: str,
        search_type: str = "vector",
        project_id: Optional[str] = None,
        top_k: int = 5,
        alpha: float = 0.5
    ) -> List[TextContent]:
        """Execute RAG search tool."""
        try:
            filters = {"project_id": project_id} if project_id else None
            
            if search_type == "vector":
                results = self.search_engine.vector_search(query, top_k=top_k, filters=filters)
            elif search_type == "keyword":
                results = self.search_engine.keyword_search(query, top_k=top_k, filters=filters)
            elif search_type == "hybrid":
                results = self.search_engine.hybrid_search(
                    query, alpha=alpha, top_k=top_k, filters=filters
                )
            else:
                raise ValueError(f"Invalid search type: {search_type}")
            
            # Format results
            result_text = self._format_search_results(results, query)
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]
    
    async def rag_index(
        self,
        path: str,
        project_id: str,
        recursive: bool = False
    ) -> List[TextContent]:
        """Execute RAG index tool."""
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                return [TextContent(type="text", text=f"Error: Path does not exist: {path}")]
            
            # Load documents
            if path_obj.is_file():
                doc = self.document_loader.load_file(path_obj)
                documents = [doc]
            else:
                documents = self.document_loader.load_directory(path_obj, recursive=recursive)
            
            if not documents:
                return [TextContent(type="text", text="No documents found to index")]
            
            # Index documents
            indexed_count = 0
            errors = []
            
            for doc in documents:
                try:
                    metadata = doc['metadata'].copy()
                    metadata['project_id'] = project_id
                    
                    self.database.add_document(
                        text=doc['content'],
                        metadata=metadata
                    )
                    indexed_count += 1
                except Exception as e:
                    errors.append(f"Failed to index {doc.get('file_info', {}).get('name', 'unknown')}: {e}")
            
            # Prepare result message
            result_parts = [f"Successfully indexed {indexed_count}/{len(documents)} documents"]
            if errors:
                result_parts.append(f"Errors:\n" + "\n".join(errors))
            
            return [TextContent(type="text", text="\n\n".join(result_parts))]
            
        except Exception as e:
            error_msg = f"Indexing failed: {str(e)}"
            logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]
    
    async def rag_suggest(
        self,
        query: str,
        limit: int = 5
    ) -> List[TextContent]:
        """Execute RAG suggest tool."""
        try:
            suggestions = self.search_engine.suggest_similar_queries(query, limit=limit)
            
            if not suggestions:
                return [TextContent(type="text", text="No suggestions found")]
            
            result_text = f"Query suggestions for '{query}':\n\n"
            for i, suggestion in enumerate(suggestions, 1):
                result_text += f"{i}. {suggestion}\n"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            error_msg = f"Suggestion generation failed: {str(e)}"
            logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]
    
    async def rag_stats(self) -> List[TextContent]:
        """Execute RAG stats tool."""
        try:
            stats = self.search_engine.get_search_statistics()
            projects = self.database.list_projects()
            
            result_text = "RAG System Statistics:\n\n"
            result_text += f"Database:\n"
            result_text += f"  • Collection: {stats['database']['collection_name']}\n"
            result_text += f"  • Documents: {stats['database']['document_count']}\n\n"
            
            result_text += f"Embedding Model:\n"
            result_text += f"  • Model: {stats['vectorizer']['model_name']}\n"
            result_text += f"  • Device: {stats['vectorizer']['device']}\n"
            result_text += f"  • Dimensions: {stats['vectorizer']['embedding_dimension']}\n\n"
            
            result_text += f"Projects ({len(projects)}):\n"
            for project in projects[:5]:
                result_text += f"  • {project['id']}: {project['document_count']} docs\n"
            
            if len(projects) > 5:
                result_text += f"  ... and {len(projects) - 5} more\n"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            error_msg = f"Statistics retrieval failed: {str(e)}"
            logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]
    
    async def _generate_search_context_prompt(
        self,
        query: str,
        max_results: int = 5
    ) -> str:
        """Generate search context prompt."""
        try:
            results = self.search_engine.vector_search(query, top_k=max_results)
            
            prompt = f"Based on the following search results for '{query}':\n\n"
            
            for i, result in enumerate(results['results'], 1):
                prompt += f"Result {i}:\n"
                prompt += f"Content: {result['text'][:500]}...\n"
                prompt += f"Source: {result['metadata'].get('file_name', 'Unknown')}\n"
                prompt += f"Project: {result['metadata'].get('project_id', 'Unknown')}\n"
                prompt += f"Relevance Score: {result['score']:.3f}\n\n"
            
            prompt += "Please provide a comprehensive answer based on these search results."
            
            return prompt
            
        except Exception as e:
            return f"Failed to generate search context: {e}"
    
    async def _generate_documentation_prompt(
        self,
        topic: str,
        project_id: Optional[str] = None
    ) -> str:
        """Generate documentation context prompt."""
        try:
            filters = {"project_id": project_id} if project_id else None
            results = self.search_engine.vector_search(
                f"documentation {topic}", 
                top_k=3, 
                filters=filters
            )
            
            prompt = f"Documentation context for '{topic}':\n\n"
            
            if results['results']:
                for i, result in enumerate(results['results'], 1):
                    prompt += f"Document {i}:\n"
                    prompt += f"{result['text'][:400]}...\n"
                    prompt += f"Source: {result['metadata'].get('file_name', 'Unknown')}\n\n"
            else:
                prompt += "No specific documentation found for this topic.\n\n"
            
            prompt += f"Please provide documentation or guidance for '{topic}' "
            prompt += f"{'in the context of project: ' + project_id if project_id else 'in general'}."
            
            return prompt
            
        except Exception as e:
            return f"Failed to generate documentation context: {e}"
    
    def _format_search_results(self, results: Dict[str, Any], query: str) -> str:
        """Format search results for text output."""
        if not results['results']:
            return f"No results found for query: '{query}'"
        
        output = f"Search Results for '{query}' ({results['search_type']} search):\n"
        output += f"Found {results['total_found']} results\n\n"
        
        for i, result in enumerate(results['results'], 1):
            output += f"{i}. {result['text'][:200]}...\n"
            output += f"   Score: {result['score']:.3f}\n"
            output += f"   File: {result['metadata'].get('file_name', 'N/A')}\n"
            output += f"   Project: {result['metadata'].get('project_id', 'N/A')}\n\n"
        
        return output
    
    async def run_stdio(self):
        """Run MCP server with stdio transport."""
        if not MCP_AVAILABLE:
            logger.error("MCP not available - cannot run server")
            raise RuntimeError("MCP packages not installed")
        
        await stdio_server(self.server)


async def main():
    """Main entry point for MCP server."""
    server = RAGMCPServer()
    await server.initialize()
    await server.run_stdio()


if __name__ == "__main__":
    asyncio.run(main())