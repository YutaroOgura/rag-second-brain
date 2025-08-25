#!/usr/bin/env python3
"""
CLIツール完全実装のテストケース
TDD（テスト駆動開発）アプローチ

テスト対象:
1. statsコマンド - 統計情報表示
2. projectsコマンド - プロジェクト一覧
3. documentsコマンド - ドキュメント一覧
4. エラーハンドリング - 構造化エラー
5. フィルタリング修正 - 正しい結果返却
"""

import json
import subprocess
import sys
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
import time

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestCLIComplete:
    """CLI完全実装のテストクラス"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスのセットアップ"""
        cls.rag_cmd = "/home/ogura/.rag/venv/bin/rag"
        cls.test_project = "test_cli"
        cls.test_dir = tempfile.mkdtemp(prefix="test_cli_")
        
        # テスト用ドキュメントを作成
        cls.test_docs = {
            "doc1.md": """# テストドキュメント1
カテゴリ: 運用
タグ: #test #cli
内容: CLIテスト用ドキュメント""",
            "doc2.md": """# API設計書
カテゴリ: 設計書
タグ: #api #design
内容: API設計のドキュメント""",
            "doc3.md": """# 運用マニュアル
カテゴリ: 運用
タグ: #operation #manual
内容: システム運用手順書"""
        }
        
        # テストドキュメントを作成
        for filename, content in cls.test_docs.items():
            filepath = Path(cls.test_dir) / filename
            filepath.write_text(content, encoding='utf-8')
    
    @classmethod
    def teardown_class(cls):
        """テストクラスのクリーンアップ"""
        import shutil
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
    
    def run_cli_command(self, *args) -> Dict[str, Any]:
        """CLIコマンドを実行して結果を返す"""
        cmd = [self.rag_cmd] + list(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # JSON出力の場合はパース
            if '--format' in args and 'json' in args:
                try:
                    return {
                        'success': True,
                        'data': json.loads(result.stdout),
                        'stderr': result.stderr,
                        'returncode': result.returncode
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'returncode': result.returncode
                    }
            else:
                return {
                    'success': result.returncode == 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timeout'
            }
    
    # ==================== statsコマンドのテスト ====================
    
    def test_stats_command_basic(self):
        """statsコマンドの基本動作テスト"""
        result = self.run_cli_command('stats')
        
        assert result['success'], f"statsコマンドが失敗: {result.get('stderr', '')}"
        assert 'RAG System Statistics' in result['stdout']
        assert 'Database:' in result['stdout']
        assert 'Collection:' in result['stdout']
        assert 'Documents:' in result['stdout']
        assert 'Embedding Model:' in result['stdout']
        assert 'Projects:' in result['stdout']
    
    def test_stats_command_json_format(self):
        """statsコマンドのJSON出力テスト"""
        result = self.run_cli_command('stats', '--format', 'json')
        
        assert result['success'], f"stats JSONコマンドが失敗: {result.get('stderr', '')}"
        
        data = result['data']
        assert 'database' in data
        assert 'collection' in data['database']
        assert 'document_count' in data['database']
        assert 'embedding_model' in data
        assert 'projects' in data
        assert isinstance(data['projects'], dict)
    
    def test_stats_with_project_filter(self):
        """statsコマンドのプロジェクトフィルタテスト"""
        # 実際に存在するプロジェクトでテスト（ultraまたはtest_project）
        result = self.run_cli_command('stats', '--project', 'ultra')
        
        assert result['success'], f"stats with projectが失敗: {result.get('stderr', '')}"
        # プロジェクトフィルタが適用されている場合、そのプロジェクトのみ表示される
        assert 'ultra' in result['stdout']
    
    # ==================== projectsコマンドのテスト ====================
    
    def test_projects_command_basic(self):
        """projectsコマンドの基本動作テスト"""
        result = self.run_cli_command('projects')
        
        assert result['success'], f"projectsコマンドが失敗: {result.get('stderr', '')}"
        assert 'Projects in Database' in result['stdout']
        assert 'Project ID' in result['stdout']
        assert 'Documents' in result['stdout']
    
    def test_projects_command_json_format(self):
        """projectsコマンドのJSON出力テスト"""
        result = self.run_cli_command('projects', '--format', 'json')
        
        assert result['success'], f"projects JSONコマンドが失敗: {result.get('stderr', '')}"
        
        data = result['data']
        assert 'projects' in data
        assert isinstance(data['projects'], list)
        
        if len(data['projects']) > 0:
            project = data['projects'][0]
            assert 'id' in project
            assert 'name' in project
            assert 'document_count' in project
    
    def test_projects_with_details(self):
        """projectsコマンドの詳細表示テスト"""
        result = self.run_cli_command('projects', '--details')
        
        assert result['success'], f"projects --detailsが失敗: {result.get('stderr', '')}"
        # 詳細情報が含まれることを確認
        assert 'Created:' in result['stdout'] or 'File types:' in result['stdout']
    
    # ==================== documentsコマンドのテスト ====================
    
    def test_documents_command_basic(self):
        """documentsコマンドの基本動作テスト"""
        result = self.run_cli_command('documents')
        
        assert result['success'], f"documentsコマンドが失敗: {result.get('stderr', '')}"
        assert 'ID:' in result['stdout'] or 'No documents' in result['stdout']
    
    def test_documents_with_project_filter(self):
        """documentsコマンドのプロジェクトフィルタテスト"""
        result = self.run_cli_command('documents', '--project', self.test_project)
        
        assert result['success'], f"documents with projectが失敗: {result.get('stderr', '')}"
    
    def test_documents_with_limit(self):
        """documentsコマンドの件数制限テスト"""
        result = self.run_cli_command('documents', '--limit', '5')
        
        assert result['success'], f"documents with limitが失敗: {result.get('stderr', '')}"
        
        # 最大5件しか表示されないことを確認
        lines = result['stdout'].split('\n')
        doc_count = sum(1 for line in lines if 'ID:' in line)
        assert doc_count <= 5, f"制限を超えるドキュメントが表示された: {doc_count}"
    
    def test_documents_json_format(self):
        """documentsコマンドのJSON出力テスト"""
        result = self.run_cli_command('documents', '--format', 'json', '--limit', '3')
        
        assert result['success'], f"documents JSONコマンドが失敗: {result.get('stderr', '')}"
        
        data = result['data']
        assert 'documents' in data
        assert isinstance(data['documents'], list)
        assert len(data['documents']) <= 3
        
        if len(data['documents']) > 0:
            doc = data['documents'][0]
            assert 'id' in doc
            assert 'metadata' in doc
            assert 'text' in doc or 'content' in doc
    
    # ==================== エラーハンドリングのテスト ====================
    
    def test_error_invalid_command(self):
        """無効なコマンドのエラーハンドリング"""
        result = self.run_cli_command('invalid_command')
        
        assert not result['success']
        assert 'No such command' in result['stderr'] or 'Error' in result['stderr']
    
    def test_error_missing_required_param(self):
        """必須パラメータ欠落のエラーハンドリング"""
        result = self.run_cli_command('search')  # queryが必須
        
        assert not result['success']
        assert 'Missing' in result['stderr'] or 'required' in result['stderr'].lower()
    
    def test_error_invalid_project(self):
        """存在しないプロジェクトのエラーハンドリング"""
        result = self.run_cli_command('documents', '--project', 'non_existent_project_xyz')
        
        # エラーまたは空の結果が返る
        assert result['success'] or 'No documents' in result['stdout']
    
    def test_structured_error_response(self):
        """構造化エラーレスポンスのテスト"""
        result = self.run_cli_command('search', 'test', '--format', 'json', '--type', 'invalid_type')
        
        if not result['success']:
            # JSONエラーレスポンスの構造を確認
            if 'data' in result:
                error_data = result['data']
                assert 'error' in error_data or 'message' in error_data
                if 'error' in error_data:
                    assert 'type' in error_data['error'] or 'message' in error_data['error']
    
    # ==================== フィルタリング修正のテスト ====================
    
    def test_filtering_with_category(self):
        """カテゴリフィルタが正しく動作することのテスト"""
        # まずインデックスを作成
        self.run_cli_command('index', self.test_dir, '--project', self.test_project, '--recursive')
        time.sleep(1)  # インデックス作成待ち
        
        # カテゴリ「運用」でフィルタリング
        result = self.run_cli_command(
            'search', '内容',
            '--project', self.test_project,
            '--filter-category', '運用',
            '--format', 'json'
        )
        
        if result['success'] and 'data' in result:
            data = result['data']
            if 'results' in data and len(data['results']) > 0:
                # フィルタリングされた結果がすべて「運用」カテゴリであることを確認
                for doc in data['results']:
                    if 'metadata' in doc and 'category' in doc['metadata']:
                        assert doc['metadata']['category'] == '運用', \
                            f"フィルタリングが正しく動作していない: {doc['metadata']['category']}"
    
    def test_filtering_with_tags(self):
        """タグフィルタが正しく動作することのテスト"""
        result = self.run_cli_command(
            'search', 'ドキュメント',
            '--project', self.test_project,
            '--filter-tags', 'test,cli',
            '--format', 'json'
        )
        
        if result['success'] and 'data' in result:
            data = result['data']
            if 'results' in data and len(data['results']) > 0:
                # フィルタリングされた結果が指定タグを含むことを確認
                for doc in data['results']:
                    if 'metadata' in doc and 'tags' in doc['metadata']:
                        doc_tags = doc['metadata']['tags']
                        assert 'test' in doc_tags or 'cli' in doc_tags, \
                            f"タグフィルタリングが正しく動作していない: {doc_tags}"
    
    def test_filtering_empty_results(self):
        """フィルタリングで結果が0件の場合の処理"""
        result = self.run_cli_command(
            'search', 'test',
            '--project', self.test_project,
            '--filter-category', '存在しないカテゴリ',
            '--format', 'json'
        )
        
        assert result['success'], "フィルタリングで0件でもエラーにならないこと"
        
        if 'data' in result:
            data = result['data']
            assert 'results' in data
            assert len(data['results']) == 0, "存在しないカテゴリでは0件になるべき"
            # total_foundが0または適切な値であることを確認
            if 'total_found' in data:
                assert data['total_found'] == 0
    
    def test_filtering_preserves_unfilterd_count(self):
        """フィルタリング前の総件数が保持されることのテスト"""
        # フィルタなしで検索
        result_no_filter = self.run_cli_command(
            'search', 'ドキュメント',
            '--project', self.test_project,
            '--format', 'json'
        )
        
        # フィルタありで検索
        result_with_filter = self.run_cli_command(
            'search', 'ドキュメント',
            '--project', self.test_project,
            '--filter-category', '運用',
            '--format', 'json'
        )
        
        if result_no_filter['success'] and result_with_filter['success']:
            if 'data' in result_no_filter and 'data' in result_with_filter:
                # フィルタ前後で適切な件数表示がされることを確認
                no_filter_count = len(result_no_filter['data'].get('results', []))
                with_filter_count = len(result_with_filter['data'].get('results', []))
                
                # フィルタリングにより件数が減ることを確認（または同じ）
                assert with_filter_count <= no_filter_count, \
                    f"フィルタリング後の件数が増えている: {with_filter_count} > {no_filter_count}"


def main():
    """テスト実行"""
    test = TestCLIComplete()
    test.setup_class()
    
    print("🧪 CLI完全実装テスト開始\n")
    
    passed = 0
    failed = 0
    
    # すべてのテストメソッドを実行
    test_methods = [
        # statsコマンド
        ('stats基本動作', test.test_stats_command_basic),
        ('stats JSON出力', test.test_stats_command_json_format),
        ('statsプロジェクトフィルタ', test.test_stats_with_project_filter),
        
        # projectsコマンド
        ('projects基本動作', test.test_projects_command_basic),
        ('projects JSON出力', test.test_projects_command_json_format),
        ('projects詳細表示', test.test_projects_with_details),
        
        # documentsコマンド
        ('documents基本動作', test.test_documents_command_basic),
        ('documentsプロジェクトフィルタ', test.test_documents_with_project_filter),
        ('documents件数制限', test.test_documents_with_limit),
        ('documents JSON出力', test.test_documents_json_format),
        
        # エラーハンドリング
        ('無効コマンドエラー', test.test_error_invalid_command),
        ('必須パラメータ欠落エラー', test.test_error_missing_required_param),
        ('無効プロジェクトエラー', test.test_error_invalid_project),
        ('構造化エラーレスポンス', test.test_structured_error_response),
        
        # フィルタリング修正
        ('カテゴリフィルタ', test.test_filtering_with_category),
        ('タグフィルタ', test.test_filtering_with_tags),
        ('フィルタ結果0件処理', test.test_filtering_empty_results),
        ('フィルタ前後の件数保持', test.test_filtering_preserves_unfilterd_count),
    ]
    
    for test_name, test_method in test_methods:
        try:
            test_method()
            print(f"✅ {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name}: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_name}: 予期しないエラー - {str(e)}")
            failed += 1
    
    test.teardown_class()
    
    print(f"\n📊 テスト結果")
    print(f"成功: {passed}")
    print(f"失敗: {failed}")
    print(f"合計: {passed + failed}")
    
    if failed > 0:
        print(f"\n⚠️  {failed}個のテストが失敗しました")
        sys.exit(1)
    else:
        print("\n✨ すべてのテストが成功しました！")


if __name__ == "__main__":
    main()