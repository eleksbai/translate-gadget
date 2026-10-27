"""全局热键管理 - 使用平台原生 API，无额外依赖"""

import sys
from typing import Callable


class HotkeyManager:
    """
    全局热键管理器

    通过平台原生 API 注册全局热键：
    - Windows: Win32 RegisterHotKey API
    - Linux: TODO（Wayland 下需探索可行方案）
    """

    def __init__(self) -> None:
        self._callback: Callable | None = None
        self._registered = False

    def register(self, hotkey_str: str, callback: Callable) -> None:
        """
        注册全局热键

        Args:
            hotkey_str: 热键字符串，如 'ctrl+alt+t'
            callback: 热键触发时的回调函数
        """
        self.unregister()
        self._callback = callback

        if sys.platform == "win32":
            self._register_windows(hotkey_str)
        else:
            self._register_linux(hotkey_str)

    def unregister(self) -> None:
        """注销已注册的热键"""
        if not self._registered:
            return

        if sys.platform == "win32":
            self._unregister_windows()
        else:
            self._unregister_linux()

        self._registered = False

    # ── Windows 实现 ──────────────────────────────────────

    def _register_windows(self, hotkey_str: str) -> None:
        """通过 Win32 RegisterHotKey API 注册全局热键"""
        import ctypes
        import ctypes.wintypes

        user32 = ctypes.windll.user32
        modifiers, vk = self._parse_hotkey_windows(hotkey_str)
        # 使用固定 ID=1 注册热键
        result = user32.RegisterHotKey(0, 1, modifiers, vk)
        if result:
            self._registered = True
        else:
            raise RuntimeError(f"注册热键失败: {hotkey_str}")

    def _unregister_windows(self) -> None:
        """注销 Win32 热键"""
        import ctypes

        ctypes.windll.user32.UnregisterHotKey(0, 1)

    @staticmethod
    def _parse_hotkey_windows(hotkey_str: str) -> tuple[int, int]:
        """
        解析热键字符串为 Windows 修饰键 + 虚拟键码

        Args:
            hotkey_str: 如 'ctrl+alt+t'

        Returns:
            (modifiers, vk_code) 元组
        """
        MOD_ALT = 0x0001
        MOD_CTRL = 0x0002
        MOD_SHIFT = 0x0004
        MOD_WIN = 0x0008

        parts = hotkey_str.lower().split("+")
        modifiers = 0
        vk = 0

        for part in parts:
            part = part.strip("<>")
            if part in ("ctrl", "control"):
                modifiers |= MOD_CTRL
            elif part == "alt":
                modifiers |= MOD_ALT
            elif part == "shift":
                modifiers |= MOD_SHIFT
            elif part in ("win", "meta"):
                modifiers |= MOD_WIN
            elif len(part) == 1:
                vk = ord(part.upper())

        return modifiers, vk

    # ── Linux 实现（TODO）──────────────────────────────────

    def _register_linux(self, hotkey_str: str) -> None:
        """
        Linux 全局热键注册（TODO）

        Wayland 下全局热键依赖合成器支持，可选方案：
        - KDE KGlobalAccel（DBus）
        - GNOME 全局快捷键
        - keybinder-3.0（XWayland 下可用）
        """
        raise NotImplementedError(
            "Linux 全局热键尚未实现，需根据桌面环境选择合适方案"
        )

    def _unregister_linux(self) -> None:
        """注销 Linux 热键"""
        pass
