"""系统托盘图标与右键菜单"""

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class TrayIcon(QSystemTrayIcon):
    """系统托盘图标"""

    def __init__(self, on_settings=None, on_quit=None) -> None:
        """
        Args:
            on_settings: 点击「设置」的回调
            on_quit: 点击「退出」的回调
        """
        super().__init__()
        self._on_settings = on_settings
        self._on_quit = on_quit

        # 占位图标（后续替换为正式设计）
        self.setIcon(QIcon.fromTheme("accessories-text-editor"))
        self.setToolTip("Translate Gadget")

        self._setup_menu()

    def _setup_menu(self) -> None:
        """创建右键菜单"""
        menu = QMenu()

        settings_action = QAction("设置", menu)
        settings_action.triggered.connect(self._handle_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self._handle_quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _handle_settings(self) -> None:
        if self._on_settings is not None:
            self._on_settings()

    def _handle_quit(self) -> None:
        if self._on_quit is not None:
            self._on_quit()
