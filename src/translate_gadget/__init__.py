"""Translate Gadget - 桌面翻译小工具"""

__version__ = "0.1.0"


def main() -> None:
    """程序入口，由 __main__.py 或 [project.scripts] 调用"""
    import logging
    import signal
    import sys

    # 恢复 Python 默认的 SIGINT 处理，确保 Ctrl+C 能够正确终止程序
    # Qt 事件循环会拦截系统信号，需要显式设置
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication, QDialog

    from translate_gadget.config import ConfigManager
    from translate_gadget.translator import AliTranslator
    from translate_gadget.window import MainWindow
    from translate_gadget.settings_dialog import SettingsDialog
    from translate_gadget.tray import TrayIcon

    app = QApplication(sys.argv)
    app.setApplicationName("Translate Gadget")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("TranslateGadget")
    app.setQuitOnLastWindowClosed(False)  # 关闭主窗口时不退出，由托盘控制

    # 设置应用图标（任务栏和窗口标题栏）
    app.setWindowIcon(QIcon.fromTheme("accessories-text-editor"))

    config_manager = ConfigManager()

    # 根据已保存的配置创建翻译器实例
    translator = None
    api_config = config_manager.load_api_config()
    if api_config["app_id"] and api_config["secret_key"]:
        translator = AliTranslator(
            access_key_id=api_config["app_id"],
            access_key_secret=api_config["secret_key"],
            region_id=ConfigManager.REGION_ID,
        )

    window = MainWindow(
        translator=translator,
        config_manager=config_manager,
    )

    # 设置对话框
    def show_settings():
        dialog = SettingsDialog(config_manager, window)
        result = dialog.exec()
        if result != QDialog.DialogCode.Accepted:
            return
        # 设置保存后重建翻译器
        nonlocal translator
        cfg = config_manager.load_api_config()
        if cfg["app_id"] and cfg["secret_key"]:
            translator = AliTranslator(
                access_key_id=cfg["app_id"],
                access_key_secret=cfg["secret_key"],
                region_id=ConfigManager.REGION_ID,
            )
            window._translator = translator
        # 同步调试配置
        debug_cfg = config_manager.load_debug_config()
        window._show_sample_border = debug_cfg.get("show_sample_border", False)
        window.update()

    window._on_settings = show_settings

    # 系统托盘
    tray = TrayIcon(on_settings=show_settings, on_quit=app.quit)
    tray.show()

    window.show()

    sys.exit(app.exec())
