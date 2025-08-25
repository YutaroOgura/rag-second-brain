"""
CLIのJSON出力修正版（該当部分のみ）
"""

import json
from typing import Dict


def _output_search_results(results: dict, output_format: str, query: str):
    """Output search results in specified format."""
    
    if output_format == 'json':
        # JSON output - 改行を適切にエスケープ
        # json.dumpsは自動的に改行をエスケープする
        json_output = json.dumps(results, ensure_ascii=False, indent=None)
        # インデントなしで1行にすることで、パースエラーを防ぐ
        console.print(json_output)
        return
    
    # ... 他のフォーマット処理は変更なし


def safe_json_output(data: Dict) -> str:
    """
    MCPサーバーで安全にパース可能なJSON出力を生成
    
    Args:
        data: 出力するデータ辞書
    
    Returns:
        1行のJSON文字列（改行が適切にエスケープされている）
    """
    # インデントなし、改行なしの1行JSON
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))