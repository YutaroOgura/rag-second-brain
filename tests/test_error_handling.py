#!/usr/bin/env python3
"""
エラーハンドリング改善のテストケース
構造化エラーレスポンスの実装

テスト対象:
1. エラータイプの分類
2. 詳細なエラーメッセージ
3. エラーコードの付与
4. リトライ可能性の情報
5. デバッグ情報の提供
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ErrorType(Enum):
    """エラータイプの定義"""
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND_ERROR = "not_found_error"
    DATABASE_ERROR = "database_error"
    PERMISSION_ERROR = "permission_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    CONFIGURATION_ERROR = "configuration_error"
    INTERNAL_ERROR = "internal_error"


class ErrorCode(Enum):
    """エラーコードの定義"""
    # 検証エラー (1000番台)
    INVALID_QUERY = 1001
    INVALID_PROJECT_ID = 1002
    INVALID_SEARCH_TYPE = 1003
    INVALID_FILTER = 1004
    MISSING_REQUIRED_PARAM = 1005
    
    # リソースエラー (2000番台)
    PROJECT_NOT_FOUND = 2001
    DOCUMENT_NOT_FOUND = 2002
    COLLECTION_NOT_FOUND = 2003
    
    # データベースエラー (3000番台)
    DB_CONNECTION_FAILED = 3001
    DB_QUERY_FAILED = 3002
    DB_WRITE_FAILED = 3003
    
    # 権限エラー (4000番台)
    INSUFFICIENT_PERMISSIONS = 4001
    AUTHENTICATION_FAILED = 4002
    
    # ネットワークエラー (5000番台)
    NETWORK_UNREACHABLE = 5001
    REQUEST_TIMEOUT = 5002
    
    # システムエラー (9000番台)
    INTERNAL_SERVER_ERROR = 9001
    CONFIGURATION_ERROR = 9002


class TestStructuredError:
    """構造化エラーのテストクラス"""
    
    def create_error_response(
        self,
        error_type: ErrorType,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict] = None,
        retryable: bool = False,
        debug_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """構造化エラーレスポンスを作成"""
        
        error = {
            "error": {
                "type": error_type.value,
                "code": error_code.value,
                "message": message,
                "retryable": retryable
            }
        }
        
        if details:
            error["error"]["details"] = details
            
        if debug_info:
            error["error"]["debug_info"] = debug_info
            
        return error
    
    # ==================== 検証エラーのテスト ====================
    
    def test_invalid_query_error(self):
        """無効なクエリのエラーレスポンス"""
        error = self.create_error_response(
            error_type=ErrorType.VALIDATION_ERROR,
            error_code=ErrorCode.INVALID_QUERY,
            message="検索クエリが無効です",
            details={
                "query": "",
                "reason": "クエリは空にできません"
            },
            retryable=False
        )
        
        assert error["error"]["type"] == "validation_error"
        assert error["error"]["code"] == 1001
        assert error["error"]["message"] == "検索クエリが無効です"
        assert error["error"]["retryable"] is False
        assert error["error"]["details"]["reason"] == "クエリは空にできません"
    
    def test_invalid_project_id_error(self):
        """無効なプロジェクトIDのエラーレスポンス"""
        error = self.create_error_response(
            error_type=ErrorType.VALIDATION_ERROR,
            error_code=ErrorCode.INVALID_PROJECT_ID,
            message="プロジェクトIDの形式が無効です",
            details={
                "project_id": "123-invalid",
                "pattern": "^[a-zA-Z0-9_-]+$",
                "reason": "プロジェクトIDには英数字、ハイフン、アンダースコアのみ使用可能です"
            },
            retryable=False
        )
        
        assert error["error"]["code"] == 1002
        assert "pattern" in error["error"]["details"]
    
    def test_missing_required_param_error(self):
        """必須パラメータ欠落のエラーレスポンス"""
        error = self.create_error_response(
            error_type=ErrorType.VALIDATION_ERROR,
            error_code=ErrorCode.MISSING_REQUIRED_PARAM,
            message="必須パラメータが不足しています",
            details={
                "missing_params": ["query", "project_id"],
                "provided_params": ["search_type", "top_k"]
            },
            retryable=False
        )
        
        assert error["error"]["code"] == 1005
        assert len(error["error"]["details"]["missing_params"]) == 2
    
    # ==================== リソースエラーのテスト ====================
    
    def test_project_not_found_error(self):
        """プロジェクトが見つからないエラー"""
        error = self.create_error_response(
            error_type=ErrorType.NOT_FOUND_ERROR,
            error_code=ErrorCode.PROJECT_NOT_FOUND,
            message="指定されたプロジェクトが見つかりません",
            details={
                "project_id": "non_existent_project",
                "available_projects": ["ultra", "test_project"]
            },
            retryable=False,
            debug_info={
                "search_path": "/home/ogura/.rag/projects",
                "timestamp": "2025-08-25T12:00:00Z"
            }
        )
        
        assert error["error"]["type"] == "not_found_error"
        assert error["error"]["code"] == 2001
        assert "available_projects" in error["error"]["details"]
        assert "search_path" in error["error"]["debug_info"]
    
    def test_document_not_found_error(self):
        """ドキュメントが見つからないエラー"""
        error = self.create_error_response(
            error_type=ErrorType.NOT_FOUND_ERROR,
            error_code=ErrorCode.DOCUMENT_NOT_FOUND,
            message="指定されたドキュメントが見つかりません",
            details={
                "document_id": "doc_xyz123",
                "project_id": "test_project"
            },
            retryable=False
        )
        
        assert error["error"]["code"] == 2002
        assert error["error"]["details"]["document_id"] == "doc_xyz123"
    
    # ==================== データベースエラーのテスト ====================
    
    def test_database_connection_error(self):
        """データベース接続エラー"""
        error = self.create_error_response(
            error_type=ErrorType.DATABASE_ERROR,
            error_code=ErrorCode.DB_CONNECTION_FAILED,
            message="データベースへの接続に失敗しました",
            details={
                "database_path": "/home/ogura/.rag/chroma",
                "error_detail": "Permission denied"
            },
            retryable=True,
            debug_info={
                "retry_count": 3,
                "max_retries": 5,
                "next_retry_in": 5
            }
        )
        
        assert error["error"]["type"] == "database_error"
        assert error["error"]["code"] == 3001
        assert error["error"]["retryable"] is True
        assert error["error"]["debug_info"]["retry_count"] == 3
    
    def test_database_query_error(self):
        """データベースクエリエラー"""
        error = self.create_error_response(
            error_type=ErrorType.DATABASE_ERROR,
            error_code=ErrorCode.DB_QUERY_FAILED,
            message="データベースクエリの実行に失敗しました",
            details={
                "query_type": "search",
                "collection": "documents",
                "error_detail": "Collection does not exist"
            },
            retryable=False
        )
        
        assert error["error"]["code"] == 3002
        assert error["error"]["details"]["collection"] == "documents"
    
    # ==================== タイムアウトエラーのテスト ====================
    
    def test_timeout_error(self):
        """タイムアウトエラー"""
        error = self.create_error_response(
            error_type=ErrorType.TIMEOUT_ERROR,
            error_code=ErrorCode.REQUEST_TIMEOUT,
            message="リクエストがタイムアウトしました",
            details={
                "timeout_seconds": 30,
                "operation": "search",
                "query": "複雑なクエリ..."
            },
            retryable=True,
            debug_info={
                "elapsed_time": 30.5,
                "suggested_timeout": 60
            }
        )
        
        assert error["error"]["type"] == "timeout_error"
        assert error["error"]["code"] == 5002
        assert error["error"]["retryable"] is True
        assert error["error"]["debug_info"]["suggested_timeout"] == 60
    
    # ==================== エラーのシリアライズテスト ====================
    
    def test_error_json_serialization(self):
        """エラーレスポンスのJSON シリアライズ"""
        error = self.create_error_response(
            error_type=ErrorType.INTERNAL_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="内部サーバーエラーが発生しました",
            details={
                "request_id": "req_123456",
                "trace_id": "trace_abcdef"
            },
            retryable=True
        )
        
        # JSONにシリアライズできることを確認
        json_str = json.dumps(error, ensure_ascii=False)
        assert json_str is not None
        
        # デシリアライズして内容を確認
        parsed = json.loads(json_str)
        assert parsed["error"]["code"] == 9001
        assert parsed["error"]["details"]["request_id"] == "req_123456"
    
    # ==================== エラーハンドラーのテスト ====================
    
    def test_error_handler_validation(self):
        """エラーハンドラーの検証ロジック"""
        def validate_error_response(error_response: Dict) -> bool:
            """エラーレスポンスの妥当性を検証"""
            if "error" not in error_response:
                return False
                
            error = error_response["error"]
            
            # 必須フィールドの確認
            required_fields = ["type", "code", "message", "retryable"]
            for field in required_fields:
                if field not in error:
                    return False
            
            # エラータイプの検証
            valid_types = [e.value for e in ErrorType]
            if error["type"] not in valid_types:
                return False
            
            # エラーコードの検証
            if not isinstance(error["code"], int) or error["code"] < 1000:
                return False
            
            return True
        
        # 正常なエラーレスポンス
        valid_error = self.create_error_response(
            error_type=ErrorType.VALIDATION_ERROR,
            error_code=ErrorCode.INVALID_QUERY,
            message="テストエラー",
            retryable=False
        )
        assert validate_error_response(valid_error) is True
        
        # 不正なエラーレスポンス
        invalid_error = {"message": "エラー"}
        assert validate_error_response(invalid_error) is False
    
    def test_error_recovery_suggestions(self):
        """エラー回復の提案情報"""
        error = self.create_error_response(
            error_type=ErrorType.CONFIGURATION_ERROR,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            message="設定ファイルが見つかりません",
            details={
                "config_path": "/home/ogura/.rag/config.yaml",
                "suggestions": [
                    "setup.sh を実行して設定ファイルを生成してください",
                    "または、config.yaml.example をコピーして設定してください"
                ]
            },
            retryable=False,
            debug_info={
                "searched_paths": [
                    "/home/ogura/.rag/config.yaml",
                    "./config.yaml",
                    "/etc/rag/config.yaml"
                ]
            }
        )
        
        assert "suggestions" in error["error"]["details"]
        assert len(error["error"]["details"]["suggestions"]) == 2
        assert "searched_paths" in error["error"]["debug_info"]


def main():
    """テスト実行"""
    test = TestStructuredError()
    
    print("🧪 構造化エラーハンドリングテスト開始\n")
    
    passed = 0
    failed = 0
    
    # すべてのテストメソッドを実行
    test_methods = [
        # 検証エラー
        ('無効クエリエラー', test.test_invalid_query_error),
        ('無効プロジェクトIDエラー', test.test_invalid_project_id_error),
        ('必須パラメータ欠落エラー', test.test_missing_required_param_error),
        
        # リソースエラー
        ('プロジェクト未検出エラー', test.test_project_not_found_error),
        ('ドキュメント未検出エラー', test.test_document_not_found_error),
        
        # データベースエラー
        ('DB接続エラー', test.test_database_connection_error),
        ('DBクエリエラー', test.test_database_query_error),
        
        # タイムアウトエラー
        ('タイムアウトエラー', test.test_timeout_error),
        
        # シリアライズ
        ('JSONシリアライズ', test.test_error_json_serialization),
        
        # エラーハンドラー
        ('エラーハンドラー検証', test.test_error_handler_validation),
        ('エラー回復提案', test.test_error_recovery_suggestions),
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