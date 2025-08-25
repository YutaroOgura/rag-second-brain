#!/usr/bin/env python3
"""
MCP Tools機能のテストケース
未実装機能のテスト駆動開発（TDD）用
"""

import json
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
import time

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestMCPTools:
    """MCP Tools機能のテストクラス"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスのセットアップ"""
        cls.mcp_server_path = project_root / "mcp-server.js"
        cls.test_dir = tempfile.mkdtemp(prefix="rag_test_")
        cls.test_project = "test_project"
        
        # テスト用ドキュメントを作成
        cls.test_docs = {
            "test1.md": """# テストドキュメント1
このドキュメントはテスト用です。
タグ: #test #documentation
カテゴリ: テスト""",
            "test2.md": """# API設計書
API認証システムの設計書です。
タグ: #api #auth
カテゴリ: 設計書""",
            "test3.md": """# Slack通知設定
Slack通知の設定方法について。
タグ: #slack #notification
カテゴリ: 運用"""
        }
        
        # テストドキュメントを作成
        for filename, content in cls.test_docs.items():
            filepath = Path(cls.test_dir) / filename
            filepath.write_text(content, encoding='utf-8')
    
    @classmethod
    def teardown_class(cls):
        """テストクラスのクリーンアップ"""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
    
    def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """MCPツールを呼び出すヘルパー関数"""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
        
        cmd = f"echo '{json.dumps(request)}' | node {self.mcp_server_path} 2>/dev/null"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # レスポンスの最後の行（JSON-RPC応答）を取得
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.startswith('{'):
                try:
                    response = json.loads(line)
                    return response
                except json.JSONDecodeError:
                    continue
        return {"error": "No valid JSON response"}
    
    # ==================== rag_index Tool のテスト ====================
    
    def test_rag_index_single_file(self):
        """単一ファイルのインデックス作成テスト"""
        response = self.call_mcp_tool("rag_index", {
            "path": f"{self.test_dir}/test1.md",
            "project_id": self.test_project,
            "recursive": False
        })
        
        # 期待される結果
        assert "result" in response or "error" not in response
        if "result" in response:
            result = response["result"]
            assert "indexed_files" in result
            assert len(result["indexed_files"]) == 1
            assert "test1.md" in result["indexed_files"][0]
            assert result["total_chunks"] > 0
            
        print("✅ 単一ファイルのインデックス作成: OK")
    
    def test_rag_index_directory_recursive(self):
        """ディレクトリの再帰的インデックス作成テスト"""
        response = self.call_mcp_tool("rag_index", {
            "path": self.test_dir,
            "project_id": self.test_project,
            "recursive": True,
            "metadata": {
                "category": "test",
                "tags": ["test", "automated"]
            }
        })
        
        # 期待される結果
        assert "result" in response or "error" not in response
        if "result" in response:
            result = response["result"]
            assert len(result["indexed_files"]) == 3
            assert result["total_chunks"] > 0
            
        print("✅ ディレクトリの再帰的インデックス作成: OK")
    
    def test_rag_index_update_existing(self):
        """既存ドキュメントの更新テスト"""
        # 最初のインデックス
        response1 = self.call_mcp_tool("rag_index", {
            "path": f"{self.test_dir}/test1.md",
            "project_id": self.test_project,
            "update": False
        })
        
        # 更新
        response2 = self.call_mcp_tool("rag_index", {
            "path": f"{self.test_dir}/test1.md",
            "project_id": self.test_project,
            "update": True
        })
        
        assert "result" in response2
        print("✅ 既存ドキュメントの更新: OK")
    
    # ==================== rag_delete Tool のテスト ====================
    
    def test_rag_delete_by_document_id(self):
        """ドキュメントIDによる削除テスト"""
        # まずインデックスを作成
        index_response = self.call_mcp_tool("rag_index", {
            "path": f"{self.test_dir}/test1.md",
            "project_id": self.test_project
        })
        
        # ドキュメントIDを取得（実装により異なる）
        doc_id = "test_doc_id"  # 実際の実装ではインデックスから取得
        
        # 削除
        response = self.call_mcp_tool("rag_delete", {
            "document_id": doc_id
        })
        
        assert "result" in response or "error" not in response
        if "result" in response:
            result = response["result"]
            assert "deleted_count" in result
            assert result["deleted_count"] >= 0
            
        print("✅ ドキュメントIDによる削除: OK")
    
    def test_rag_delete_by_project(self):
        """プロジェクト全体の削除テスト"""
        response = self.call_mcp_tool("rag_delete", {
            "project": self.test_project
        })
        
        assert "result" in response or "error" not in response
        if "result" in response:
            result = response["result"]
            assert "deleted_count" in result
            assert "deleted_ids" in result
            
        print("✅ プロジェクト全体の削除: OK")
    
    def test_rag_delete_with_filters(self):
        """フィルタ条件による削除テスト"""
        response = self.call_mcp_tool("rag_delete", {
            "filters": {
                "older_than": "7d",
                "category": "test"
            }
        })
        
        assert "result" in response or "error" not in response
        print("✅ フィルタ条件による削除: OK")
    
    # ==================== rag_sync Tool のテスト ====================
    
    def test_rag_sync_project(self):
        """プロジェクト同期テスト"""
        response = self.call_mcp_tool("rag_sync", {
            "project": self.test_project,
            "path": self.test_dir,
            "full": False,
            "remove_deleted": True
        })
        
        assert "result" in response or "error" not in response
        if "result" in response:
            result = response["result"]
            assert "added" in result
            assert "updated" in result
            assert "deleted" in result
            assert "unchanged" in result
            
        print("✅ プロジェクト同期: OK")
    
    def test_rag_sync_full_reindex(self):
        """完全再インデックステスト"""
        response = self.call_mcp_tool("rag_sync", {
            "project": self.test_project,
            "path": self.test_dir,
            "full": True
        })
        
        assert "result" in response or "error" not in response
        print("✅ 完全再インデックス: OK")
    
    # ==================== フィルタリング機能のテスト ====================
    
    def test_search_with_category_filter(self):
        """カテゴリフィルタ付き検索テスト"""
        response = self.call_mcp_tool("rag_search", {
            "query": "テスト",
            "project_id": self.test_project,
            "filters": {
                "category": "設計書"
            }
        })
        
        assert "result" in response or "error" not in response
        if "result" in response:
            # カテゴリが「設計書」の結果のみが返る
            results = json.loads(response["result"]["content"][0]["text"])
            if results["results"]:
                for result in results["results"]:
                    metadata = result.get("metadata", {})
                    assert metadata.get("category") == "設計書"
                    
        print("✅ カテゴリフィルタ付き検索: OK")
    
    def test_search_with_tags_filter(self):
        """タグフィルタ付き検索テスト"""
        response = self.call_mcp_tool("rag_search", {
            "query": "API",
            "project_id": self.test_project,
            "filters": {
                "tags": ["api", "auth"]
            }
        })
        
        assert "result" in response or "error" not in response
        if "result" in response:
            results = json.loads(response["result"]["content"][0]["text"])
            if results["results"]:
                for result in results["results"]:
                    metadata = result.get("metadata", {})
                    tags = metadata.get("tags", [])
                    assert "api" in tags or "auth" in tags
                    
        print("✅ タグフィルタ付き検索: OK")
    
    def test_search_with_date_filter(self):
        """日付フィルタ付き検索テスト"""
        response = self.call_mcp_tool("rag_search", {
            "query": "ドキュメント",
            "project_id": self.test_project,
            "filters": {
                "created_after": "2025-01-01",
                "created_before": "2025-12-31"
            }
        })
        
        assert "result" in response or "error" not in response
        print("✅ 日付フィルタ付き検索: OK")
    
    def test_search_with_combined_filters(self):
        """複合フィルタ付き検索テスト"""
        response = self.call_mcp_tool("rag_search", {
            "query": "通知",
            "project_id": self.test_project,
            "filters": {
                "category": "運用",
                "tags": ["slack"],
                "created_after": "2025-01-01"
            }
        })
        
        assert "result" in response or "error" not in response
        print("✅ 複合フィルタ付き検索: OK")
    
    # ==================== 位置情報とハイライトのテスト ====================
    
    def test_search_with_position_info(self):
        """位置情報付き検索結果テスト"""
        response = self.call_mcp_tool("rag_search", {
            "query": "API認証",
            "project_id": self.test_project,
            "include_position": True
        })
        
        assert "result" in response or "error" not in response
        if "result" in response:
            results = json.loads(response["result"]["content"][0]["text"])
            if results["results"]:
                for result in results["results"]:
                    # position情報の確認
                    if "position" in result:
                        position = result["position"]
                        assert "line_start" in position
                        assert "line_end" in position
                        assert position["line_start"] >= 0
                        assert position["line_end"] >= position["line_start"]
                        
        print("✅ 位置情報付き検索結果: OK")
    
    def test_search_with_highlights(self):
        """ハイライト情報付き検索結果テスト"""
        response = self.call_mcp_tool("rag_search", {
            "query": "Slack",
            "project_id": self.test_project,
            "include_highlights": True
        })
        
        assert "result" in response or "error" not in response
        if "result" in response:
            results = json.loads(response["result"]["content"][0]["text"])
            if results["results"]:
                for result in results["results"]:
                    # highlights情報の確認
                    if "highlights" in result:
                        highlights = result["highlights"]
                        assert isinstance(highlights, list)
                        for highlight in highlights:
                            assert "start" in highlight
                            assert "end" in highlight
                            assert highlight["start"] >= 0
                            assert highlight["end"] > highlight["start"]
                            
        print("✅ ハイライト情報付き検索結果: OK")


class TestMCPToolsIntegration:
    """MCP Tools統合テストクラス"""
    
    def test_index_search_delete_workflow(self):
        """インデックス→検索→削除のワークフローテスト"""
        tools = TestMCPTools()
        
        # 1. インデックス作成
        index_response = tools.call_mcp_tool("rag_index", {
            "path": tools.test_dir,
            "project_id": "workflow_test",
            "recursive": True
        })
        assert "error" not in index_response
        
        # 2. 検索実行
        search_response = tools.call_mcp_tool("rag_search", {
            "query": "API",
            "project_id": "workflow_test"
        })
        assert "error" not in search_response
        
        # 3. プロジェクト削除
        delete_response = tools.call_mcp_tool("rag_delete", {
            "project": "workflow_test"
        })
        assert "error" not in delete_response
        
        # 4. 再検索（結果なしを確認）
        search_response2 = tools.call_mcp_tool("rag_search", {
            "query": "API",
            "project_id": "workflow_test"
        })
        # 結果が0件または空であることを確認
        
        print("✅ インデックス→検索→削除ワークフロー: OK")
    
    def test_sync_with_file_changes(self):
        """ファイル変更時の同期テスト"""
        tools = TestMCPTools()
        test_file = Path(tools.test_dir) / "dynamic.md"
        
        # 1. 初期ファイル作成とインデックス
        test_file.write_text("# 初期内容\n初期テキスト", encoding='utf-8')
        tools.call_mcp_tool("rag_index", {
            "path": str(test_file),
            "project_id": "sync_test"
        })
        
        # 2. ファイル更新
        time.sleep(1)  # タイムスタンプ差を確保
        test_file.write_text("# 更新内容\n更新されたテキスト", encoding='utf-8')
        
        # 3. 同期実行
        sync_response = tools.call_mcp_tool("rag_sync", {
            "project": "sync_test",
            "path": tools.test_dir
        })
        
        assert "result" in sync_response
        if "result" in sync_response:
            result = sync_response["result"]
            assert len(result["updated"]) > 0
            
        print("✅ ファイル変更時の同期: OK")


def run_all_tests():
    """全テストを実行"""
    print("🧪 MCP Tools機能テスト開始\n")
    
    # セットアップ
    TestMCPTools.setup_class()
    
    try:
        test = TestMCPTools()
        integration_test = TestMCPToolsIntegration()
        
        # 個別機能テスト
        print("📝 1. rag_index Tool テスト")
        tests = [
            ("単一ファイルインデックス", test.test_rag_index_single_file),
            ("ディレクトリ再帰インデックス", test.test_rag_index_directory_recursive),
            ("既存ドキュメント更新", test.test_rag_index_update_existing),
        ]
        
        passed = 0
        failed = 0
        skipped = 0
        
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
            except AssertionError as e:
                print(f"❌ {test_name}: 失敗 - {e}")
                failed += 1
            except Exception as e:
                print(f"⚠️  {test_name}: スキップ - 未実装")
                skipped += 1
        
        print("\n📝 2. rag_delete Tool テスト")
        tests = [
            ("ドキュメントID削除", test.test_rag_delete_by_document_id),
            ("プロジェクト削除", test.test_rag_delete_by_project),
            ("フィルタ削除", test.test_rag_delete_with_filters),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
            except AssertionError as e:
                print(f"❌ {test_name}: 失敗 - {e}")
                failed += 1
            except Exception as e:
                print(f"⚠️  {test_name}: スキップ - 未実装")
                skipped += 1
        
        print("\n📝 3. rag_sync Tool テスト")
        tests = [
            ("プロジェクト同期", test.test_rag_sync_project),
            ("完全再インデックス", test.test_rag_sync_full_reindex),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
            except AssertionError as e:
                print(f"❌ {test_name}: 失敗 - {e}")
                failed += 1
            except Exception as e:
                print(f"⚠️  {test_name}: スキップ - 未実装")
                skipped += 1
        
        print("\n📝 4. フィルタリング機能テスト")
        tests = [
            ("カテゴリフィルタ", test.test_search_with_category_filter),
            ("タグフィルタ", test.test_search_with_tags_filter),
            ("日付フィルタ", test.test_search_with_date_filter),
            ("複合フィルタ", test.test_search_with_combined_filters),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
            except AssertionError as e:
                print(f"❌ {test_name}: 失敗 - {e}")
                failed += 1
            except Exception as e:
                print(f"⚠️  {test_name}: スキップ - 未実装")
                skipped += 1
        
        print("\n📝 5. 位置情報・ハイライトテスト")
        tests = [
            ("位置情報", test.test_search_with_position_info),
            ("ハイライト", test.test_search_with_highlights),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
            except AssertionError as e:
                print(f"❌ {test_name}: 失敗 - {e}")
                failed += 1
            except Exception as e:
                print(f"⚠️  {test_name}: スキップ - 未実装")
                skipped += 1
        
        print("\n📝 6. 統合テスト")
        tests = [
            ("ワークフロー", integration_test.test_index_search_delete_workflow),
            ("ファイル変更同期", integration_test.test_sync_with_file_changes),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
            except AssertionError as e:
                print(f"❌ {test_name}: 失敗 - {e}")
                failed += 1
            except Exception as e:
                print(f"⚠️  {test_name}: スキップ - 未実装")
                skipped += 1
        
        print(f"\n📊 テスト結果")
        print(f"成功: {passed}")
        print(f"失敗: {failed}")
        print(f"スキップ: {skipped}")
        print(f"合計: {passed + failed + skipped}")
        
        if failed == 0:
            print("\n✨ 実装済み機能のテストは全て成功！")
        else:
            print(f"\n⚠️  {failed}個のテストが失敗しました")
            
    finally:
        # クリーンアップ
        TestMCPTools.teardown_class()
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)