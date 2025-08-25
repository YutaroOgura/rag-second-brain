#!/usr/bin/env python3
"""
JSON出力のテストケース
改行文字のエスケープが正しく行われることを確認
"""

import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.json_output_fix import safe_json_dumps, format_search_results, validate_json_output


class TestJSONOutput:
    """JSON出力のテストクラス"""
    
    def test_simple_json_output(self):
        """シンプルなJSON出力のテスト"""
        data = {"key": "value", "number": 123}
        json_str = safe_json_dumps(data)
        
        # JSONとして有効か確認
        assert validate_json_output(json_str)
        
        # パース可能か確認
        parsed = json.loads(json_str)
        assert parsed["key"] == "value"
        assert parsed["number"] == 123
        
        print("✅ シンプルなJSON出力: OK")
    
    def test_newline_escaping(self):
        """改行文字のエスケープテスト"""
        data = {
            "text": "Line 1\nLine 2\nLine 3",
            "mixed": "Tab\there\r\nWindows line",
            "japanese": "日本語\n改行\nテスト"
        }
        
        json_str = safe_json_dumps(data)
        
        # JSONとして有効か確認
        assert validate_json_output(json_str)
        
        # パース後に元のデータと一致するか確認
        parsed = json.loads(json_str)
        assert parsed["text"] == data["text"]
        assert parsed["mixed"] == data["mixed"]
        assert parsed["japanese"] == data["japanese"]
        
        print("✅ 改行文字のエスケープ: OK")
    
    def test_complex_search_results(self):
        """複雑な検索結果のテスト"""
        results = [
            {
                "text": "# Slack通知システム設計書\n\n## 概要\nUltra PayシステムのSlack通知機能について説明します。\n\n## Slack通知の種類\n\n### 1. システムアラート通知\n- エラー発生時の即時通知\n- システム障害アラート",
                "score": 0.95,
                "metadata": {
                    "file_name": "slack_notification.md",
                    "project": "ultra",
                    "tags": ["slack", "notification", "alert"]
                }
            },
            {
                "text": "## API認証システム\n\n### JWT認証\n```php\n$token = JWT::encode($payload, $key);\n```\n\n### 認証フロー\n1. ユーザーがログイン\n2. サーバーがJWTトークンを発行",
                "score": 0.87,
                "metadata": {
                    "file_name": "api_auth.md",
                    "project": "ultra"
                }
            }
        ]
        
        formatted = format_search_results(results, "Slack", "hybrid")
        json_str = safe_json_dumps(formatted)
        
        # JSONとして有効か確認
        assert validate_json_output(json_str)
        
        # パース可能か確認
        parsed = json.loads(json_str)
        assert parsed["query"] == "Slack"
        assert parsed["search_type"] == "hybrid"
        assert len(parsed["results"]) == 2
        assert parsed["total_found"] == 2
        
        # 改行が保持されているか確認
        first_result = parsed["results"][0]
        assert "\n" in first_result["text"]
        assert "Slack通知システム設計書" in first_result["text"]
        
        print("✅ 複雑な検索結果: OK")
    
    def test_special_characters(self):
        """特殊文字のテスト"""
        data = {
            "quotes": 'He said "Hello"',
            "backslash": "C:\\Users\\path",
            "unicode": "絵文字😀テスト",
            "control": "Bell\x07character",
            "mixed": '{"nested": "json\nwith\nnewlines"}'
        }
        
        json_str = safe_json_dumps(data)
        
        # JSONとして有効か確認
        assert validate_json_output(json_str)
        
        # パース後に元のデータと一致するか確認
        parsed = json.loads(json_str)
        assert parsed["quotes"] == data["quotes"]
        assert parsed["backslash"] == data["backslash"]
        assert parsed["unicode"] == data["unicode"]
        
        print("✅ 特殊文字の処理: OK")
    
    def test_empty_and_null(self):
        """空データとnullのテスト"""
        data = {
            "empty_string": "",
            "empty_list": [],
            "empty_dict": {},
            "null_value": None,
            "results": []
        }
        
        json_str = safe_json_dumps(data)
        
        # JSONとして有効か確認
        assert validate_json_output(json_str)
        
        # パース可能か確認
        parsed = json.loads(json_str)
        assert parsed["empty_string"] == ""
        assert parsed["empty_list"] == []
        assert parsed["empty_dict"] == {}
        assert parsed["null_value"] is None
        assert parsed["results"] == []
        
        print("✅ 空データとnull: OK")
    
    def test_large_text_with_code(self):
        """コードブロックを含む大きなテキストのテスト"""
        large_text = """# Docker環境設定ガイド

## 概要
Docker環境の構築と設定について説明します。

## Dockerfile例

```dockerfile
FROM php:8.1-fpm

# Install dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    libpng-dev \\
    libonig-dev \\
    libxml2-dev \\
    zip \\
    unzip

# Install PHP extensions
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd

# Set working directory
WORKDIR /var/www
```

## docker-compose.yml

```yaml
version: '3.8'
services:
  app:
    build: .
    volumes:
      - ./:/var/www
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

## 使用方法

1. Dockerをインストール
2. `docker-compose up -d`を実行
3. http://localhost:8080 にアクセス
"""
        
        data = {
            "results": [
                {
                    "text": large_text,
                    "score": 0.92,
                    "metadata": {"file": "docker_guide.md"}
                }
            ],
            "query": "Docker",
            "total_found": 1
        }
        
        json_str = safe_json_dumps(data)
        
        # JSONとして有効か確認
        assert validate_json_output(json_str)
        
        # パース可能か確認
        parsed = json.loads(json_str)
        assert len(parsed["results"]) == 1
        assert "Docker環境設定ガイド" in parsed["results"][0]["text"]
        assert "```dockerfile" in parsed["results"][0]["text"]
        assert "```yaml" in parsed["results"][0]["text"]
        
        print("✅ コードブロックを含む大きなテキスト: OK")


def run_all_tests():
    """全テストを実行"""
    print("🧪 JSON出力テスト開始\n")
    
    test = TestJSONOutput()
    
    tests = [
        ("シンプルなJSON出力", test.test_simple_json_output),
        ("改行文字のエスケープ", test.test_newline_escaping),
        ("複雑な検索結果", test.test_complex_search_results),
        ("特殊文字の処理", test.test_special_characters),
        ("空データとnull", test.test_empty_and_null),
        ("コードブロックを含む大きなテキスト", test.test_large_text_with_code)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: 失敗 - {e}")
            failed += 1
    
    print(f"\n📊 テスト結果")
    print(f"成功: {passed}/{len(tests)}")
    print(f"失敗: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✨ 全テスト成功！")
        return True
    else:
        print("\n⚠️  一部のテストが失敗しました")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)