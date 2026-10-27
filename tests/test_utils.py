"""utils 模块单元测试"""

from translate_gadget.utils import detect_language


class TestDetectLanguage:
    """语言检测测试"""

    def test_chinese_text(self) -> None:
        assert detect_language("你好世界") == "zh"

    def test_english_text(self) -> None:
        assert detect_language("Hello World") == "en"

    def test_mixed_chinese_dominant(self) -> None:
        """中文为主的混合文本"""
        assert detect_language("这个feature不错") == "zh"

    def test_mixed_english_dominant(self) -> None:
        """英文为主的混合文本"""
        assert detect_language("This is 测试 text with some 中文") == "en"

    def test_empty_text(self) -> None:
        """空文本默认返回英文"""
        assert detect_language("") == "en"

    def test_only_numbers(self) -> None:
        """纯数字无中英文字符，默认返回英文"""
        assert detect_language("12345") == "en"
