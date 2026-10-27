"""翻译历史管理 - 内存缓存，程序退出后清空"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class HistoryRecord:
    """单条翻译记录"""

    source_text: str
    target_text: str
    source_lang: str
    target_lang: str
    timestamp: datetime = field(default_factory=datetime.now)


class HistoryManager:
    """翻译历史管理器，基于内存缓存"""

    def __init__(self, max_count: int = 1000) -> None:
        self.max_count = max_count
        self._records: deque[HistoryRecord] = deque(maxlen=max_count)

    def add_record(
        self,
        source_text: str,
        target_text: str,
        source_lang: str,
        target_lang: str,
    ) -> HistoryRecord:
        """添加一条翻译记录，超出上限时自动淘汰最早的记录"""
        record = HistoryRecord(
            source_text=source_text,
            target_text=target_text,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        self._records.appendleft(record)
        return record

    def get_records(self) -> list[HistoryRecord]:
        """获取所有历史记录（按时间倒序）"""
        return list(self._records)

    def clear(self) -> None:
        """清空所有历史记录"""
        self._records.clear()

    @property
    def count(self) -> int:
        """当前记录数"""
        return len(self._records)
