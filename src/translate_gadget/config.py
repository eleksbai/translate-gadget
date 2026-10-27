"""配置管理模块 - 使用 QSettings 持久化存储"""

from PySide6.QtCore import QSettings


class ConfigManager:
    """管理应用配置的读写与持久化"""

    SETTINGS_ORG = "TranslateGadget"
    SETTINGS_APP = "TranslateGadget"

    # 默认值
    DEFAULT_HOTKEY = "<ctrl>+<alt>+t"

    def __init__(self) -> None:
        self.settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

    # ── API 配置 ──────────────────────────────────────────

    # 硬编码常量
    API_URL = "https://mt.aliyuncs.com"
    REGION_ID = "cn-hangzhou"

    def save_api_config(self, app_id: str, secret_key: str) -> None:
        self.settings.setValue("api/app_id", app_id)
        self.settings.setValue("api/secret_key", secret_key)
        self.settings.sync()

    def load_api_config(self) -> dict:
        return {
            "app_id": self.settings.value("api/app_id", ""),
            "secret_key": self.settings.value("api/secret_key", ""),
        }

    # ── 快捷键 ────────────────────────────────────────────

    def save_hotkey(self, hotkey_str: str) -> None:
        self.settings.setValue("hotkey", hotkey_str)
        self.settings.sync()

    def load_hotkey(self) -> str:
        return self.settings.value("hotkey", self.DEFAULT_HOTKEY)

    # ── 调试 ────────────────────────────────────────────

    def save_debug_config(self, show_sample_border: bool) -> None:
        self.settings.setValue("debug/show_sample_border", show_sample_border)
        self.settings.sync()

    def load_debug_config(self) -> dict:
        return {
            "show_sample_border": self.settings.value(
                "debug/show_sample_border", False, type=bool
            ),
        }
