#!/usr/bin/env python3
"""测试 QScreen.grabWindow(0) 在当前 Wayland/X11 环境下是否可用"""

import sys
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("grabWindow 测试工具")
        self.setFixedSize(400, 350)
        self._timer = None
        self._count = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.info_label = QLabel("点击下方按钮测试截屏")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("font-size: 13px; padding: 4px;")
        layout.addWidget(self.info_label)

        self.pixmap_label = QLabel()
        self.pixmap_label.setFixedSize(380, 180)
        self.pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pixmap_label.setStyleSheet("border: 1px solid #aaa; background: #222;")
        layout.addWidget(self.pixmap_label)

        btn_layout = QVBoxLayout()

        self.single_btn = QPushButton("单次截屏测试")
        self.single_btn.clicked.connect(self._test_single)
        btn_layout.addWidget(self.single_btn)

        self.cont_btn = QPushButton("开始连续截屏（每秒1次）")
        self.cont_btn.clicked.connect(self._toggle_continuous)
        btn_layout.addWidget(self.cont_btn)

        layout.addLayout(btn_layout)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.status_label)

    def _grab_screen(self) -> QPixmap | None:
        """截取整个屏幕"""
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return None
        # grabWindow(0) 截取整个根窗口（即整个屏幕）
        return screen.grabWindow(0)

    def _test_single(self):
        """单次截屏测试"""
        pixmap = self._grab_screen()
        self._count += 1

        if pixmap is None or pixmap.isNull():
            self.info_label.setText(
                f"第 {self._count} 次截屏：<b style='color:red'>失败</b><br>"
                "grabWindow(0) 返回空 QPixmap，当前环境不支持直接截屏"
            )
            self.pixmap_label.setPixmap(QPixmap())
            self.pixmap_label.setText("截屏失败")
            return

        # 截屏成功，缩放显示
        self.info_label.setText(
            f"第 {self._count} 次截屏：<b style='color:green'>成功</b><br>"
            f"分辨率: {pixmap.width()}×{pixmap.height()}<br>"
            f"下方显示截取到的屏幕内容（缩略图）"
        )
        self._show_thumbnail(pixmap)

    def _show_thumbnail(self, pixmap: QPixmap):
        """将截屏结果缩放显示"""
        target = self.pixmap_label.size()
        scaled = pixmap.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.pixmap_label.setPixmap(scaled)
        self.pixmap_label.setText("")

    def _toggle_continuous(self):
        """切换连续截屏"""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
            self.cont_btn.setText("开始连续截屏（每秒1次）")
            self.status_label.setText("已停止")
        else:
            self._count = 0
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._continuous_grab)
            self._timer.start(1000)  # 每秒一次
            self.cont_btn.setText("停止连续截屏")
            self.status_label.setText("连续截屏中…")
            # 立即执行一次
            self._continuous_grab()

    def _continuous_grab(self):
        """连续截屏回调"""
        pixmap = self._grab_screen()
        self._count += 1

        if pixmap is None or pixmap.isNull():
            self.status_label.setText(
                f"第 {self._count} 次：<b style='color:red'>失败</b> — "
                "连续截屏不可用"
            )
            self._timer.stop()
            self._timer = None
            self.cont_btn.setText("开始连续截屏（每秒1次）")
            return

        self.status_label.setText(
            f"第 {self._count} 次截屏成功 | "
            f"{pixmap.width()}×{pixmap.height()}"
        )
        self._show_thumbnail(pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TestWindow()
    win.show()
    sys.exit(app.exec())
