#!/usr/bin/env python3
"""
JSON出力の修正用モジュール
改行文字を適切にエスケープしてJSON出力する
"""

import json
from typing import Any, Dict, List
import re


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    安全なJSON出力を行う
    
    Args:
        obj: JSONに変換するオブジェクト
        **kwargs: json.dumpsに渡す追加パラメータ
    
    Returns:
        適切にエスケープされたJSON文字列
    """
    # デフォルトパラメータを設定
    defaults = {
        'ensure_ascii': False,
        'indent': 2,
        'separators': (',', ': ')
    }
    defaults.update(kwargs)
    
    # 標準のjson.dumpsを使用（これが最も安全）
    return json.dumps(obj, **defaults)


def format_search_results(results: List[Dict], query: str, search_type: str = 'hybrid') -> Dict:
    """
    検索結果を適切にフォーマットする
    
    Args:
        results: 検索結果のリスト
        query: 検索クエリ
        search_type: 検索タイプ
    
    Returns:
        フォーマット済みの結果辞書
    """
    # 結果をクリーンアップ
    cleaned_results = []
    for result in results:
        if 'text' in result:
            # テキスト内の制御文字を適切に処理
            text = result['text']
            # 既存の不正な改行を修正
            text = text.replace('\n\n', '\n')
            text = text.replace('\r\n', '\n')
            
            cleaned_result = {
                'text': text,
                'score': result.get('score', 0.0),
                'metadata': result.get('metadata', {}),
                'file_path': result.get('file_path', 'unknown')
            }
            cleaned_results.append(cleaned_result)
    
    return {
        'query': query,
        'search_type': search_type,
        'results': cleaned_results,
        'total_found': len(cleaned_results)
    }


def validate_json_output(json_str: str) -> bool:
    """
    JSON文字列が有効かチェックする
    
    Args:
        json_str: チェックするJSON文字列
    
    Returns:
        有効な場合True
    """
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError as e:
        print(f"JSON validation error: {e}")
        return False


if __name__ == "__main__":
    # テスト用のデータ
    test_data = {
        "results": [
            {
                "text": "# Slack通知システム設計書\n\n## 概要\nUltra PayシステムのSlack通知機能について説明します。",
                "score": 0.95,
                "metadata": {"file_name": "slack_notification.md"}
            }
        ],
        "query": "Slack",
        "total_found": 1
    }
    
    # 安全なJSON出力
    json_output = safe_json_dumps(test_data)
    print("Safe JSON output:")
    print(json_output)
    
    # 検証
    is_valid = validate_json_output(json_output)
    print(f"\nJSON is valid: {is_valid}")