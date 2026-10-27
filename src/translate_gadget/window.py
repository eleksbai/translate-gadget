"""主窗口模块 - 透明背景、置顶、穿透、可拖拽、动态取色"""

import asyncio
import colorsys
import logging
import time

from PySide6.QtCore import QThread, Signal, Qt, QEvent, QPoint, QTimer
from PySide6.QtGui import QShortcut, QKeySequence, QColor, QGuiApplication, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from translate_gadget.utils import detect_language

# 邻近色色相偏移（度）
ANALOGOUS_OFFSET = 30
# 采样边距（像素）：窗口四周保留的全透明区域宽度
SAMPLE_MARGIN = 20

logger = logging.getLogger(__name__)


class _TranslateWorker(QThread):
    """在独立线程中运行异步翻译，避免阻塞 UI"""

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, translator, text, source_lang, target_lang, parent=None):
        super().__init__(parent)
        self._translator = translator
        self._text = text
        self._source_lang = source_lang
        self._target_lang = target_lang

    def run(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                self._translator.translate(
                    self._text, self._source_lang, self._target_lang
                )
            )
            loop.close()
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QWidget):
    """翻译主窗口"""

    def __init__(self, translator=None, config_manager=None, on_settings=None, parent=None) -> None:
        super().__init__(parent)
        self._translator = translator
        self._config_manager = config_manager
        self._on_settings = on_settings
        self._worker: _TranslateWorker | None = None
        self._dragging = False
        self._drag_pos = QPoint()
        # 动态取色状态
        self._dark_bg = True
        self._current_hue = 210.0  # 默认蓝色调
        self._current_sat = 0.3
        self._current_light = 0.5
        self._sampled_bg_color = (240, 240, 240)  # 默认浅灰色
        # 调试配置
        self._show_sample_border = False
        if config_manager:
            debug_cfg = config_manager.load_debug_config()
            self._show_sample_border = debug_cfg.get("show_sample_border", False)
        self._setup_window_flags()
        self._setup_ui()
        self._setup_shortcuts()
        # 在输入框上安装事件过滤器，用于 Ctrl+左键拖拽窗口
        self.input_edit.installEventFilter(self)
        # 每秒采样定时器
        self._color_timer = QTimer(self)
        self._color_timer.timeout.connect(self._sample_and_update)

    def _setup_window_flags(self) -> None:
        """配置窗口属性：无边框、置顶、透明"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 确保窗口可以接收输入法事件
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)

    def paintEvent(self, event) -> None:
        """窗口本身不绘制背景；调试模式下绘制采样区边界指示线"""
        super().paintEvent(event)
        if not self._show_sample_border:
            return
        cr = self.layout().contentsRect()
        if cr.width() <= 0 or cr.height() <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 外边缘：实线（窗口外框 = 采样区外边界）
        outer_pen = QPen(QColor(100, 100, 100, 120), 1, Qt.PenStyle.SolidLine)
        painter.setPen(outer_pen)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        # 内边缘：虚线（控件起始位置 = 采样区内边界）
        inner_pen = QPen(QColor(100, 100, 100, 100), 1, Qt.PenStyle.DashLine)
        painter.setPen(inner_pen)
        painter.drawRect(cr.adjusted(0, 0, -1, -1))
        painter.end()

    def showEvent(self, event) -> None:
        """窗口首次显示时启动颜色采样"""
        super().showEvent(event)
        self._adjust_input_width()
        if not self._color_timer.isActive():
            self._sample_and_update()
            self._color_timer.start(1000)

    def _setup_ui(self) -> None:
        """初始化界面布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SAMPLE_MARGIN, SAMPLE_MARGIN, SAMPLE_MARGIN, SAMPLE_MARGIN)

        # 输入框
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Enter text to translate...")
        self.input_edit.returnPressed.connect(self._do_translate)
        self.input_edit.textChanged.connect(self._adjust_input_width)
        # 显式启用输入法支持， ubuntu 使用 ibus输入法
        # self.input_edit.setInputMethodHints(
        #     Qt.InputMethodHint.ImhNone | Qt.InputMethodHint.ImhPreferLatin
        # )
        layout.addWidget(self.input_edit)

        # 翻译结果区域（初始隐藏，只读单行，无边框全透明，文字可复制）
        self.result_label = QLineEdit()
        self.result_label.setReadOnly(True)
        self.result_label.setVisible(False)
        layout.addWidget(self.result_label)

        # 默认位置：屏幕底部居中
        self._move_to_bottom_center()
        # 初始化输入框宽度
        self._adjust_input_width()

    def _setup_shortcuts(self) -> None:
        """注册快捷键"""
        # F4 打开设置页面
        shortcut = QShortcut(QKeySequence(Qt.Key.Key_F4), self)
        shortcut.activated.connect(self._open_settings)
        
        # Ctrl+Enter 清空输入框和翻译结果
        clear_shortcut = QShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Return), self)
        clear_shortcut.activated.connect(self._clear_input)
    
    def _clear_input(self) -> None:
        """清空输入框和翻译结果"""
        self.input_edit.clear()
        self.result_label.clear()
        self.result_label.setVisible(False)

    def _open_settings(self) -> None:
        """打开设置对话框"""
        if self._on_settings is not None:
            self._on_settings()

    def _move_to_bottom_center(self) -> None:
        """将窗口移动到屏幕底部居中"""
        from PySide6.QtWidgets import QApplication

        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        x = (geometry.width() - self.width()) // 2 + geometry.x()
        y = geometry.bottom() - self.height() - 50
        self.move(x, y)

    def _adjust_input_width(self) -> None:
        """根据文本内容自动调整输入框宽度，保证内容完整展示"""
        text = self.input_edit.text() or self.input_edit.placeholderText()
        fm = QFontMetrics(self.input_edit.font())
        # 文本宽度 + 内边距(左右各4px) + 边框(左右各1px) + 余量
        text_width = fm.horizontalAdvance(text)
        padding = 4 * 2 + 1 * 2 + 8  # padding + border + 余量
        new_width = max(200, text_width + padding)
        self.input_edit.setFixedWidth(new_width)

    def _adjust_result_width(self) -> None:
        """根据翻译结果文本内容自动调整结果区域宽度"""
        text = self.result_label.text()
        if not text:
            self.result_label.setFixedWidth(0)
            return
        fm = QFontMetrics(self.result_label.font())
        text_width = fm.horizontalAdvance(text)
        padding = 4 * 2 + 1 * 2 + 8
        self.result_label.setFixedWidth(max(200, text_width + padding))

    def show_and_focus(self) -> None:
        """显示窗口并聚焦输入框（由热键回调调用）"""
        self.show()
        self.activateWindow()
        self.raise_()
        self.input_edit.setFocus()

    # ── 动态取色 ─────────────────────────────────────────

    def _sample_and_update(self) -> None:
        """从窗口四周的全透明边距区域采样背景色，更新配色方案"""
        if self._dragging:
            return
        t0 = time.perf_counter()
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = self.frameGeometry()
        if geo.width() == 0 or geo.height() == 0:
            return

        t1 = time.perf_counter()
        # 直接抓取窗口区域，避免抓取整个屏幕再裁剪
        pixmap = screen.grabWindow(0, geo.x(), geo.y(), geo.width(), geo.height())
        t2 = time.perf_counter()

        if pixmap.isNull():
            logger.warning("grabWindow 返回空 pixmap")
            return

        img = pixmap.toImage()
        t3 = time.perf_counter()

        r, g, b = self._sample_border_colors(img)
        t4 = time.perf_counter()

        # 直接使用采样到的 RGB 值，避免 HSL 转换带来的颜色偏差
        self._sampled_bg_color = (r, g, b)
        self._current_hue, self._current_sat, self._current_light = self._rgb_to_hsl(r, g, b)
        self._dark_bg = self._current_light < 0.5
        self._apply_analogous_scheme()
        t5 = time.perf_counter()

        logger.info(
            "取色耗时: 总计 %.1fms | grabWindow %.1fms | 边缘采样 %.1fms | 配色 %.1fms | "
            "RGB(%d,%d,%d) HSL(%.0f,%.2f,%.2f) dark=%s",
            (t5 - t0) * 1000,
            (t2 - t1) * 1000,
            (t4 - t3) * 1000,
            (t5 - t4) * 1000,
            r, g, b,
            self._current_hue, self._current_sat, self._current_light,
            self._dark_bg,
        )

    def _sample_border_colors(self, img) -> tuple[int, int, int]:
        """从布局边距区域（全透明）采样背景主色调

        利用 layout.contentsRect() 确定控件起始位置，
        仅从边距范围内采样，避开子控件的半透明区域。
        自动调整采样步长，控制总采样点数不超过 1 万。
        按频率取前 70% 的数据进行平均，过滤异常颜色。
        """
        w, h = img.width(), img.height()
        if w == 0 or h == 0:
            return (128, 128, 128)

        cr = self.layout().contentsRect()
        # 边距宽度（图片坐标）
        ml = cr.left()
        mr = w - cr.right()
        mt = cr.top()
        mb = h - cr.bottom()

        # 四个不重叠的边距矩形: (x1, y1, x2, y2)
        rects = [
            (0, 0, w, mt),                   # 上边距
            (0, h - mb, w, h),               # 下边距
            (0, mt, ml, h - mb),             # 左边距（排除上下角）
            (w - mr, mt, w, h - mb),         # 右边距（排除上下角）
        ]

        # 预估总采样点数（step=1 时）
        total_pixels = sum((rx2 - rx1) * (ry2 - ry1) for rx1, ry1, rx2, ry2 in rects)

        # 自动调整 step，控制采样点数不超过 1 万
        MAX_SAMPLES = 10000
        step = 1
        if total_pixels > MAX_SAMPLES:
            step = max(1, int((total_pixels / MAX_SAMPLES) ** 0.5))

        # 采样所有像素，统计颜色频率
        color_freq: dict[tuple[int, int, int], int] = {}
        total_count = 0
        for rx1, ry1, rx2, ry2 in rects:
            for y in range(ry1, ry2, step):
                for x in range(rx1, rx2, step):
                    if 0 <= x < w and 0 <= y < h:
                        c = QColor(img.pixel(x, y))
                        rgb = (c.red(), c.green(), c.blue())
                        color_freq[rgb] = color_freq.get(rgb, 0) + 1
                        total_count += 1

        if total_count == 0:
            return (128, 128, 128)

        # 按频率降序排序
        sorted_colors = sorted(color_freq.items(), key=lambda x: x[1], reverse=True)

        # 取前 70% 的数据（按频率累加）
        target_count = int(total_count * 0.7)
        r_sum = g_sum = b_sum = count = 0
        for rgb, freq in sorted_colors:
            if count >= target_count:
                break
            r_sum += rgb[0] * freq
            g_sum += rgb[1] * freq
            b_sum += rgb[2] * freq
            count += freq

        if count == 0:
            return (128, 128, 128)
        return (r_sum // count, g_sum // count, b_sum // count)

    @staticmethod
    def _extract_dominant_color(img) -> tuple[int, int, int]:
        """从 QImage 中提取平均主色调"""
        w, h = img.width(), img.height()
        if w == 0 or h == 0:
            return (128, 128, 128)
        step = max(1, (w * h) // 400)  # 采样约 400 个像素
        r_sum = g_sum = b_sum = count = 0
        for y in range(0, h, step):
            for x in range(0, w, step):
                c = QColor(img.pixel(x, y))
                r_sum += c.red()
                g_sum += c.green()
                b_sum += c.blue()
                count += 1
        if count == 0:
            return (128, 128, 128)
        return (r_sum // count, g_sum // count, b_sum // count)

    @staticmethod
    def _rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
        """RGB → (H: 0-360, S: 0-1, L: 0-1)"""
        h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        return (h * 360.0, s, l)

    def _apply_analogous_scheme(self) -> None:
        """根据采样色相生成邻近色方案并应用到所有控件"""
        h = self._current_hue
        s = self._current_sat
        l = self._current_light
        dark = self._dark_bg

        # 邻近色：色相 -30°（用于边框）
        h1 = (h - ANALOGOUS_OFFSET) % 360

        # 边框色：邻近色1，饱和度适中
        border_r, border_g, border_b = colorsys.hls_to_rgb(
            h1 / 360.0, 0.45 if dark else 0.40, min(s + 0.2, 0.7)
        )
        br, bg, bb = int(border_r * 255), int(border_g * 255), int(border_b * 255)

        # 背景色：直接使用采样到的 RGB 值，与采样区域颜色完全一致
        bg_r, bg_g, bg_b = self._sampled_bg_color

        # 文字色
        if dark:
            tc = "white"
            hc = "rgba(255,255,255,180)"
        else:
            tc = "#1a1a1a"
            hc = "rgba(0,0,0,140)"

        border = f"rgba({br},{bg},{bb},120)"

        # 窗口本身不绘制背景（全透明），由 paintEvent 留空实现
        self.setStyleSheet("MainWindow { background-color: transparent; }")

        # 输入框：不透明背景（与采样区域颜色一致），无边框
        panel_bg = f"rgb({bg_r},{bg_g},{bg_b})"
        input_style = (
            f"QLineEdit {{ background-color: {panel_bg}; border: none;"
            f" border-radius: 4px; padding: 4px; color: {tc}; }}"
            f"QLineEdit::placeholder {{ color: {hc}; }}"
        )
        self.input_edit.setStyleSheet(input_style)
        
        # 翻译结果区域：与输入框样式保持一致
        self.result_label.setStyleSheet(input_style)
        self._adjust_result_width()
        self.update()

    # ── Ctrl+左键拖拽窗口 ─────────────────────────────────

    def eventFilter(self, obj, event) -> bool:
        """拦截输入框的鼠标事件：Ctrl+左键拖拽移动窗口，双击清空输入"""
        if obj is self.input_edit:
            # 确保输入法事件能够正常传递
            if event.type() in (
                QEvent.Type.InputMethod,
                QEvent.Type.InputMethodQuery,
                QEvent.Type.FocusIn,
                QEvent.Type.FocusOut,
                QEvent.Type.FocusAboutToChange,
            ):
                return super().eventFilter(obj, event)
            if event.type() == QEvent.Type.MouseButtonDblClick:
                self.input_edit.clear()
                return True
            if event.type() == QEvent.Type.MouseButtonPress:
                if (
                    event.button() == Qt.MouseButton.LeftButton
                    and event.modifiers() & Qt.KeyboardModifier.ControlModifier
                ):
                    self._dragging = True
                    # 记录鼠标全局位置与窗口位置的偏移
                    self._drag_pos = event.globalPosition().toPoint() - self.pos()
                    return True  # 消费事件，不传给输入框
            elif event.type() == QEvent.Type.MouseMove and self._dragging:
                # 根据鼠标全局位置更新窗口位置
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if self._dragging:
                    self._dragging = False
                    return True
        return super().eventFilter(obj, event)

    # ── 翻译流程 ─────────────────────────────────────────

    def _do_translate(self) -> None:
        """触发翻译：检测语言方向 → 启动异步翻译线程"""
        text = self.input_edit.text().strip()
        if not text or self._translator is None:
            return

        source_lang = detect_language(text)
        target_lang = "en" if source_lang == "zh" else "zh"

        self.input_edit.setEnabled(False)
        self.input_edit.setPlaceholderText("Translating...")

        self._worker = _TranslateWorker(
            self._translator, text, source_lang, target_lang
        )
        self._worker.finished.connect(self._on_translate_done)
        self._worker.error.connect(self._on_translate_error)
        self._worker.start()

    def _on_translate_done(self, result: str) -> None:
        """翻译成功回调"""
        self.input_edit.setEnabled(True)
        self.input_edit.setPlaceholderText("Enter text to translate...")
        self.result_label.setText(result)
        self.result_label.setVisible(True)
        self._adjust_result_width()

    def _on_translate_error(self, error_msg: str) -> None:
        """翻译失败回调"""
        self.input_edit.setEnabled(True)
        self.input_edit.setPlaceholderText("Enter text to translate...")
        self.result_label.setText(f"Translation failed: {error_msg}")
        self.result_label.setVisible(True)
        self._adjust_result_width()
