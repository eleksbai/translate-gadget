"""history 模块单元测试"""

from translate_gadget.history import HistoryManager


class TestHistoryManager:
    """翻译历史管理测试"""

    def test_add_record(self) -> None:
        manager = HistoryManager(max_count=10)
        record = manager.add_record("你好", "Hello", "zh", "en")
        assert record.source_text == "你好"
        assert record.target_text == "Hello"
        assert manager.count == 1

    def test_max_count_limit(self) -> None:
        manager = HistoryManager(max_count=3)
        for i in range(5):
            manager.add_record(f"src_{i}", f"tgt_{i}", "zh", "en")
        assert manager.count == 3
        # 最新的在前面
        records = manager.get_records()
        assert records[0].source_text == "src_4"

    def test_clear(self) -> None:
        manager = HistoryManager()
        manager.add_record("test", "test", "zh", "en")
        manager.clear()
        assert manager.count == 0

    def test_get_records_order(self) -> None:
        manager = HistoryManager()
        manager.add_record("first", "第一", "en", "zh")
        manager.add_record("second", "第二", "en", "zh")
        records = manager.get_records()
        assert records[0].source_text == "second"
        assert records[1].source_text == "first"
