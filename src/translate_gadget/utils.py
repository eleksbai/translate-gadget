"""工具函数模块"""

import re


def detect_language(text: str) -> str:
    """
    检测输入文本的主要语言方向

    按字符比例判定：统计中文字符与英文字符的占比，
    中文字符多则判定为中文，反之判定为英文。

    Args:
        text: 待检测的文本

    Returns:
        语言代码：'zh' 表示中文，'en' 表示英文
    """
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    english_chars = len(re.findall(r"[a-zA-Z]", text))

    if chinese_chars >= english_chars:
        return "zh"
    return "en"
