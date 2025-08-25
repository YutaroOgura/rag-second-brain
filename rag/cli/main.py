"""Main CLI entry point for RAG system"""
import click
import json
import hashlib
from pathlib import Path
from datetime import datetime
from ..core import DatabaseManager, SearchEngine

@click.group()
def cli():
    """RAG Second Brain CLI"""
    pass

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--project', '-p', required=True, help='Project ID')
@click.option('--recursive', '-r', is_flag=True, help='Recursively index directories')
@click.option('--update', '-u', is_flag=True, help='Update existing documents')
@click.option('--format', 'output_format', default='text', type=click.Choice(['text', 'json']))
def index(path, project, recursive, update, output_format):
    """Index documents into the RAG system"""
    try:
        path_obj = Path(path)
        indexed_count = 0
        skipped_count = 0
        error_count = 0
        
        # ファイルリストを取得
        if path_obj.is_file():
            files = [path_obj]
        elif path_obj.is_dir():
            if recursive:
                files = list(path_obj.rglob('*'))
            else:
                files = list(path_obj.glob('*'))
            files = [f for f in files if f.is_file()]
        else:
            raise ValueError(f"Invalid path: {path}")
        
        # 対象ファイルのフィルタリング（テキストファイルのみ）
        text_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.rst', '.log'}
        files = [f for f in files if f.suffix.lower() in text_extensions]
        
        if output_format == 'text':
            click.echo(f"Indexing {len(files)} files from {path} into project '{project}'...")
        
        db = DatabaseManager()
        
        for file_path in files:
            try:
                # ファイル内容を読み込み
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if not content.strip():
                    skipped_count += 1
                    continue
                
                # ドキュメントIDを生成（ファイルパスのハッシュ）
                doc_id = f"doc_{hashlib.md5(str(file_path).encode()).hexdigest()[:16]}"
                
                # メタデータを作成
                stat = file_path.stat()
                metadata = {
                    'file_path': str(file_path.absolute()),
                    'file_name': file_path.name,
                    'project_id': project,
                    'file_size': stat.st_size,
                    'modified_at': stat.st_mtime,
                    'created_at': datetime.now().isoformat(),
                    'file_extension': file_path.suffix,
                    'line_count': content.count('\n') + 1,
                    'char_count': len(content),
                    'word_count': len(content.split())
                }
                
                # ChromaDBに追加または更新
                if update:
                    # 更新モード: upsertを使用（存在すれば更新、なければ追加）
                    collection = db.db.get_or_create_collection("documents")
                    collection.upsert(
                        documents=[content[:8000]],  # 8000文字に制限
                        metadatas=[metadata],
                        ids=[doc_id]
                    )
                    indexed_count += 1
                else:
                    # 通常モード: 既存チェックしてから追加
                    collection = db.db.get_or_create_collection("documents")
                    existing = collection.get(ids=[doc_id])
                    
                    if existing and existing['ids']:
                        # 既に存在する場合はスキップ
                        skipped_count += 1
                        if output_format == 'text':
                            click.echo(f"  Skipped (already indexed): {file_path.name}")
                    else:
                        # 新規追加
                        collection.add(
                            documents=[content[:8000]],  # 8000文字に制限
                            metadatas=[metadata],
                            ids=[doc_id]
                        )
                        indexed_count += 1
                
            except Exception as e:
                error_count += 1
                if output_format == 'text':
                    click.echo(f"  Error indexing {file_path}: {e}")
        
        # 結果を出力
        result = {
            'success': True,
            'project': project,
            'indexed': indexed_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total_files': len(files)
        }
        
        if output_format == 'json':
            click.echo(json.dumps(result, ensure_ascii=False))
        else:
            click.echo(f"\nIndexing complete:")
            click.echo(f"  Indexed: {indexed_count} files")
            click.echo(f"  Skipped: {skipped_count} files")
            click.echo(f"  Errors: {error_count} files")
            click.echo(f"  Total documents in database: {db.get_stats()['total_documents']}")
    
    except Exception as e:
        error = {
            'success': False,
            'error': str(e)
        }
        if output_format == 'json':
            click.echo(json.dumps(error, ensure_ascii=False))
        else:
            click.echo(f"Error: {e}")

@cli.command()
@click.argument('query')
@click.option('--project', '-p', help='Project ID')
@click.option('--type', '-t', default='hybrid', help='Search type')
@click.option('--top-k', '-k', default=5, help='Number of results')
def search(query, project, type, top_k):
    """Search documents"""
    db = DatabaseManager()
    engine = SearchEngine(db)
    
    results = engine.search(
        query=query,
        search_type=type,
        top_k=top_k,
        project_id=project
    )
    
    for i, result in enumerate(results, 1):
        click.echo(f"\n{i}. {result['text'][:200]}...")
        if result.get('metadata'):
            click.echo(f"   Metadata: {result['metadata']}")

@cli.command()
def stats():
    """Show statistics"""
    db = DatabaseManager()
    stats = db.get_stats()
    
    click.echo(f"Total documents: {stats['total_documents']}")
    click.echo(f"Collections: {', '.join(stats['collections'])}")

@cli.command()
def projects():
    """List projects"""
    db = DatabaseManager()
    projects = db.list_projects()
    
    if projects:
        click.echo("Projects:")
        for project in projects:
            click.echo(f"  - {project}")
    else:
        click.echo("No projects found")

if __name__ == '__main__':
    cli()