#!/usr/bin/env python3
"""测试 PySide6 中文输入法支持 - 最简版本"""

import sys
from PySide6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget


def main():
    """主函数 - 创建一个简单的窗口和输入框"""
    app = QApplication(sys.argv)
    
    # 创建窗口
    window = QWidget()
    window.setWindowTitle("中文输入法测试")
    window.resize(400, 100)
    
    # 创建布局
    layout = QVBoxLayout(window)
    
    # 创建输入框
    input_edit = QLineEdit()
    input_edit.setPlaceholderText("在这里输入中文...")
    input_edit.setStyleSheet(
        "QLineEdit { background-color: white; border: 2px solid black; "
        "padding: 8px; font-size: 14px; }"
    )
    layout.addWidget(input_edit)
    
    # 显示窗口
    window.show()
    
    print("窗口已打开，请尝试输入中文")
    print("按 Ctrl+C 退出")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
