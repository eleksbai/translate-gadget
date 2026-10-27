"""设置对话框 - 配置翻译 API 参数和快捷键"""

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, config_manager, parent=None) -> None:
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._load_config()

    def _setup_ui(self) -> None:
        """初始化对话框布局"""
        layout = QVBoxLayout(self)

        # 表单区域
        form = QFormLayout()

        self.app_id_edit = QLineEdit()
        self.app_id_edit.setPlaceholderText("AccessKey ID")
        form.addRow("AccessKey ID:", self.app_id_edit)

        self.secret_key_edit = QLineEdit()
        self.secret_key_edit.setPlaceholderText("AccessKey Secret")
        self.secret_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("AccessKey Secret:", self.secret_key_edit)

        layout.addLayout(form)

        # 调试选项
        debug_group = QGroupBox("调试")
        debug_layout = QVBoxLayout()
        self.show_border_cb = QCheckBox("显示采样区域边界")
        debug_layout.addWidget(self.show_border_cb)
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)

        # 按钮区域
        btn_layout = QHBoxLayout()

        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self._test_connection)
        btn_layout.addWidget(self.test_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def _load_config(self) -> None:
        """从 ConfigManager 加载当前配置到表单"""
        config = self.config_manager.load_api_config()
        self.app_id_edit.setText(config["app_id"])
        self.secret_key_edit.setText(config["secret_key"])

        debug_cfg = self.config_manager.load_debug_config()
        self.show_border_cb.setChecked(debug_cfg.get("show_sample_border", False))

    def _save_config(self) -> None:
        """保存表单内容到 ConfigManager"""
        self.config_manager.save_api_config(
            app_id=self.app_id_edit.text().strip(),
            secret_key=self.secret_key_edit.text().strip(),
        )
        self.config_manager.save_debug_config(
            show_sample_border=self.show_border_cb.isChecked(),
        )
        self.accept()

    def _test_connection(self) -> None:
        """测试 API 连接（TODO: 接入实际翻译 API）"""
        pass
