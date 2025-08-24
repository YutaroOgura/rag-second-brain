"""Main CLI commands for RAG system."""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from ..core.database import DatabaseManager
from ..core.vectorizer import Vectorizer
from ..core.search import SearchEngine
from ..utils.document_loader import DocumentLoader
from ..utils.config import load_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rich console for formatted output
console = Console()


def detect_project_from_path(file_path: str) -> Optional[str]:
    """Detect project ID from file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected project ID or None
    """
    path = Path(file_path)
    
    # Look for common project indicators
    current = path.parent
    while current != current.parent:
        # Check for common project files
        if any((current / indicator).exists() for indicator in [
            "package.json", "Cargo.toml", "setup.py", "pom.xml",
            ".git", "README.md", "pyproject.toml"
        ]):
            return current.name
        current = current.parent
    
    return None


@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def cli(config: Optional[str], verbose: bool):
    """RAG Document Management System
    
    「第2の脳」- システム開発のためのドキュメント管理・検索システム
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Store config path in click context
    ctx = click.get_current_context()
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config


@cli.command()
@click.argument('query', required=True)
@click.option('--project', '-p', help='Filter by project ID')
@click.option('--type', '-t', 'search_type', 
              type=click.Choice(['vector', 'keyword', 'hybrid']), 
              default='vector', help='Search type')
@click.option('--top-k', '-k', default=5, help='Number of results to return')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['table', 'json', 'simple']),
              default='table', help='Output format')
@click.option('--alpha', default=0.5, type=float, 
              help='Hybrid search weight (0.0=vector, 1.0=keyword)')
def search(query: str, project: Optional[str], search_type: str, 
           top_k: int, output_format: str, alpha: float):
    """Search documents in the RAG system"""
    
    if not query or not query.strip():
        console.print("[red]Error: Query cannot be empty[/red]")
        sys.exit(1)
    
    try:
        # Load configuration
        ctx = click.get_current_context()
        config = load_config(ctx.obj.get('config_path'))
        
        # Initialize components
        console.print(f"[blue]Initializing RAG system...[/blue]")
        
        db_config = config.get('database', {})
        database = DatabaseManager(db_config.get('path', './data/chroma'))
        database.create_collection(db_config.get('collection_name', 'documents'))
        
        emb_config = config.get('embedding', {})
        vectorizer = Vectorizer(
            model_name=emb_config.get('model', 'sentence-transformers/multilingual-e5-base'),
            device=emb_config.get('device', 'cpu')
        )
        
        search_engine = SearchEngine(database, vectorizer)
        
        # Perform search
        console.print(f"[blue]Searching for: '{query}'[/blue]")
        
        filters = {"project_id": project} if project else None
        
        if search_type == 'vector':
            results = search_engine.vector_search(query, top_k=top_k, filters=filters)
        elif search_type == 'keyword':
            results = search_engine.keyword_search(query, top_k=top_k, filters=filters)
        elif search_type == 'hybrid':
            results = search_engine.hybrid_search(query, alpha=alpha, top_k=top_k, filters=filters)
        
        # Output results
        _output_search_results(results, output_format, query)
        
    except Exception as e:
        console.print(f"[red]Error during search: {e}[/red]")
        logger.error(f"Search failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument('path', required=True)
@click.option('--project', '-p', help='Project ID for the documents')
@click.option('--recursive', '-r', is_flag=True, help='Process directory recursively')
@click.option('--auto-detect-project', is_flag=True, 
              help='Auto-detect project from file path')
@click.option('--chunk-size', default=1000, help='Chunk size for documents')
@click.option('--chunk-overlap', default=200, help='Chunk overlap size')
def index(path: str, project: Optional[str], recursive: bool, 
          auto_detect_project: bool, chunk_size: int, chunk_overlap: int):
    """Index documents into the RAG system"""
    
    path_obj = Path(path)
    
    if not path_obj.exists():
        console.print(f"[red]Error: File or directory does not exist: {path}[/red]")
        sys.exit(1)
    
    try:
        # Load configuration
        ctx = click.get_current_context()
        config = load_config(ctx.obj.get('config_path'))
        
        # Initialize components
        console.print("[blue]Initializing RAG system...[/blue]")
        
        db_config = config.get('database', {})
        database = DatabaseManager(db_config.get('path', './data/chroma'))
        database.create_collection(db_config.get('collection_name', 'documents'))
        
        document_loader = DocumentLoader()
        
        # Determine project ID
        if auto_detect_project and not project:
            project = detect_project_from_path(path)
            if project:
                console.print(f"[green]Auto-detected project: {project}[/green]")
        
        # Load documents
        if path_obj.is_file():
            if not document_loader.is_supported_file(path_obj):
                console.print(f"[yellow]Warning: File format not supported: {path_obj.suffix}[/yellow]")
                sys.exit(1)
            
            console.print(f"[blue]Loading file: {path}[/blue]")
            doc = document_loader.load_file(path_obj)
            documents = [doc]
        else:
            console.print(f"[blue]Loading directory: {path} (recursive={recursive})[/blue]")
            documents = document_loader.load_directory(path_obj, recursive=recursive)
        
        if not documents:
            console.print("[yellow]No documents found to index[/yellow]")
            return
        
        # Index documents
        indexed_count = 0
        for doc in documents:
            try:
                # Prepare metadata
                metadata = doc['metadata'].copy()
                if project:
                    metadata['project_id'] = project
                
                # Add document to database
                doc_id = database.add_document(
                    text=doc['content'],
                    metadata=metadata
                )
                indexed_count += 1
                
                console.print(f"[green]✓[/green] Indexed: {doc['file_info']['name']}")
                
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to index {doc.get('file_info', {}).get('name', 'unknown')}: {e}")
                continue
        
        console.print(f"[green]Successfully indexed {indexed_count} files[/green]")
        
    except Exception as e:
        console.print(f"[red]Error during indexing: {e}[/red]")
        logger.error(f"Indexing failed: {e}")
        sys.exit(1)


@cli.command()
def projects():
    """List all projects in the database"""
    
    try:
        # Load configuration
        ctx = click.get_current_context()
        config = load_config(ctx.obj.get('config_path'))
        
        # Initialize database
        db_config = config.get('database', {})
        database = DatabaseManager(db_config.get('path', './data/chroma'))
        database.create_collection(db_config.get('collection_name', 'documents'))
        
        # Get projects
        projects_list = database.list_projects()
        
        if not projects_list:
            console.print("[yellow]No projects found in database[/yellow]")
            return
        
        # Display projects table
        table = Table(title="Projects in Database")
        table.add_column("Project ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Documents", justify="right", style="magenta")
        
        for project in projects_list:
            table.add_row(
                project['id'],
                project['name'],
                str(project['document_count'])
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing projects: {e}[/red]")
        logger.error(f"Project listing failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument('project_id')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def delete_project(project_id, confirm):
    """Delete all documents for a specific project"""
    console = Console()
    
    # Initialize database
    console.print("Initializing database...")
    config = load_config()
    db_path = config.get('database', {}).get('path', '~/.rag/chroma')
    db_manager = DatabaseManager(db_path)
    
    # Get documents for this project
    collection = db_manager.create_collection()
    
    # Query for documents with this project_id
    results = collection.get(
        where={"project_id": project_id}
    )
    
    if not results or not results['ids']:
        console.print(f"[yellow]No documents found for project: {project_id}[/yellow]")
        return
    
    doc_count = len(results['ids'])
    console.print(f"[yellow]Found {doc_count} documents for project: {project_id}[/yellow]")
    
    # Confirmation
    if not confirm:
        if not click.confirm(f"Are you sure you want to delete all {doc_count} documents for project '{project_id}'?"):
            console.print("[red]Deletion cancelled[/red]")
            return
    
    # Delete documents
    console.print(f"Deleting {doc_count} documents...")
    collection.delete(ids=results['ids'])
    
    console.print(f"[green]✓ Successfully deleted {doc_count} documents for project: {project_id}[/green]")


@cli.command()
@click.option('--project', '-p', help='Filter by project ID')
@click.option('--limit', '-l', default=10, help='Maximum number of documents to show')
def documents(project: Optional[str], limit: int):
    """List documents in the database"""
    
    try:
        # Load configuration
        ctx = click.get_current_context()
        config = load_config(ctx.obj.get('config_path'))
        
        # Initialize database
        db_config = config.get('database', {})
        database = DatabaseManager(db_config.get('path', './data/chroma'))
        database.create_collection(db_config.get('collection_name', 'documents'))
        
        # Get documents
        docs = database.list_documents(limit=limit)
        
        if project:
            docs = [doc for doc in docs if doc.get('metadata', {}).get('project_id') == project]
        
        if not docs:
            console.print("[yellow]No documents found[/yellow]")
            return
        
        # Display documents table
        table = Table(title=f"Documents in Database{f' (Project: {project})' if project else ''}")
        table.add_column("ID", style="cyan")
        table.add_column("Project", style="green")
        table.add_column("File", style="yellow")
        table.add_column("Size", justify="right", style="magenta")
        
        for doc in docs:
            metadata = doc.get('metadata', {})
            table.add_row(
                doc['id'][:12] + "...",  # Truncate ID
                metadata.get('project_id', 'N/A'),
                metadata.get('file_name', 'N/A'),
                str(len(doc.get('text', '')))
            )
        
        console.print(table)
        console.print(f"\n[blue]Showing {len(docs)} documents[/blue]")
        
    except Exception as e:
        console.print(f"[red]Error listing documents: {e}[/red]")
        logger.error(f"Document listing failed: {e}")
        sys.exit(1)


@cli.command()
def stats():
    """Show system statistics"""
    
    try:
        # Load configuration
        ctx = click.get_current_context()
        config = load_config(ctx.obj.get('config_path'))
        
        # Initialize components
        db_config = config.get('database', {})
        database = DatabaseManager(db_config.get('path', './data/chroma'))
        database.create_collection(db_config.get('collection_name', 'documents'))
        
        emb_config = config.get('embedding', {})
        vectorizer = Vectorizer(
            model_name=emb_config.get('model', 'sentence-transformers/multilingual-e5-base'),
            device=emb_config.get('device', 'cpu')
        )
        
        search_engine = SearchEngine(database, vectorizer)
        
        # Get statistics
        stats_data = search_engine.get_search_statistics()
        
        # Display statistics
        console.print("\n[bold blue]RAG System Statistics[/bold blue]")
        
        # Database stats
        console.print(f"\n[bold]Database:[/bold]")
        console.print(f"  Collection: {stats_data['database']['collection_name']}")
        console.print(f"  Documents: {stats_data['database']['document_count']}")
        
        # Vectorizer stats
        console.print(f"\n[bold]Embedding Model:[/bold]")
        console.print(f"  Model: {stats_data['vectorizer']['model_name']}")
        console.print(f"  Device: {stats_data['vectorizer']['device']}")
        console.print(f"  Dimensions: {stats_data['vectorizer']['embedding_dimension']}")
        
        # Projects
        projects_list = database.list_projects()
        console.print(f"\n[bold]Projects:[/bold] {len(projects_list)}")
        for project in projects_list[:5]:  # Show top 5
            console.print(f"  • {project['id']}: {project['document_count']} docs")
        
        if len(projects_list) > 5:
            console.print(f"  ... and {len(projects_list) - 5} more")
        
    except Exception as e:
        console.print(f"[red]Error getting statistics: {e}[/red]")
        logger.error(f"Statistics failed: {e}")
        sys.exit(1)


def _output_search_results(results: dict, output_format: str, query: str):
    """Output search results in specified format."""
    
    if output_format == 'json':
        # JSON output
        console.print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    
    if not results['results']:
        console.print("[yellow]No results found[/yellow]")
        return
    
    if output_format == 'simple':
        # Simple text output
        console.print(f"\nFound {results['total_found']} results for '{query}':\n")
        for i, result in enumerate(results['results'], 1):
            console.print(f"{i}. {result['text'][:100]}...")
            console.print(f"   Score: {result['score']:.3f}")
            console.print(f"   File: {result['metadata'].get('file_name', 'N/A')}")
            console.print()
    else:
        # Table output (default)
        table = Table(title=f"Search Results for '{query}' ({results['search_type']} search)")
        table.add_column("Rank", justify="right", style="cyan")
        table.add_column("Score", justify="right", style="green")
        table.add_column("Content", style="white")
        table.add_column("File", style="yellow")
        table.add_column("Project", style="magenta")
        
        for i, result in enumerate(results['results'], 1):
            # Truncate content for display
            content = result['text'][:80] + "..." if len(result['text']) > 80 else result['text']
            content_text = Text(content)
            
            # Highlight query terms (simple highlighting)
            query_words = query.lower().split()
            for word in query_words:
                if word in content.lower():
                    # Rich library version compatibility fix
                    try:
                        content_text.highlight_regex(
                            rf'\b{re.escape(word)}\b', 
                            style="bold yellow"
                        )
                    except TypeError:
                        # Fallback for older versions
                        content_text.highlight_words(
                            [word],
                            style="bold yellow",
                            case_sensitive=False
                        )
            
            table.add_row(
                str(i),
                f"{result['score']:.3f}",
                content_text,
                result['metadata'].get('file_name', 'N/A'),
                result['metadata'].get('project_id', 'N/A')
            )
        
        console.print(table)
        console.print(f"\n[blue]Found {results['total_found']} results[/blue]")


if __name__ == '__main__':
    cli()