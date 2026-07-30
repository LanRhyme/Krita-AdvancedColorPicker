import math
import json
from krita import *
from .qt_compat import *
from .lucide_icons import get_lucide_icon

class ColorSwatchWidget(QWidget):
    """双色对比无缝矩形色块 (左: 当前新颜色, 右: 历史原颜色，0 缝隙极致易对比)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_color = QColor(255, 255, 255)
        self.previous_color = QColor(200, 200, 200)

    def setColors(self, curr, prev):
        self.current_color = QColor(curr)
        self.previous_color = QColor(prev)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(RenderHint_Antialiasing)
        w = self.width()
        h = self.height()
        half_w = w / 2.0
        
        # 1. 建立整体外边缘 6px 圆角剪裁路径
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 6, 6)
        painter.setClipPath(path)

        # 2. 左半部分: 新颜色 (0px 缝隙)
        painter.setPen(QPen(Color_transparent))
        painter.fillRect(QRectF(0, 0, half_w, h), self.current_color)

        # 3. 右半部分: 旧颜色 (0px 缝隙无缝对接)
        painter.fillRect(QRectF(half_w, 0, half_w, h), self.previous_color)

        # 4. 外圈微边框
        painter.setClipping(False)
        painter.setPen(QPen(QColor(128, 128, 128, 60), 1))
        painter.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 6, 6)


class ColorPreviewPopup(QFrame):
    """精简 Pigment.O 灵感风格 Morandi 色彩对比 HUD 浮窗"""
    def __init__(self, parent=None):
        flags = (
            getattr(Qt, 'ToolTip', getattr(getattr(Qt, 'WindowType', None), 'ToolTip', 0)) |
            getattr(Qt, 'FramelessWindowHint', getattr(getattr(Qt, 'WindowType', None), 'FramelessWindowHint', 0))
        )
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.setFixedSize(200, 125)

        self.card = QFrame(self)
        self.card.setObjectName("ColorCard")
        self.card.setFixedSize(200, 125)

        self.refresh_theme_styles()

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. 顶栏：新旧双色无缝对比
        self.swatch = ColorSwatchWidget(self.card)
        self.swatch.setFixedHeight(46)
        layout.addWidget(self.swatch)

        # 2. 中间：HEX 标示
        self.hex_label = QLabel("#FFFFFF", self.card)
        self.hex_label.setAlignment(AlignCenter)
        self.hex_label.setStyleSheet("font-size: 14px; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(self.hex_label)

        # 3. 底部：RGB / HSV 参数
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)

        self.rgb_label = QLabel("RGB: 255, 255, 255", self.card)
        self.rgb_label.setAlignment(AlignCenter)
        self.rgb_label.setStyleSheet("font-size: 11px; opacity: 0.85;")

        self.hsv_label = QLabel("HSV: 0°, 0%, 100%", self.card)
        self.hsv_label.setAlignment(AlignCenter)
        self.hsv_label.setStyleSheet("font-size: 11px; opacity: 0.85;")

        info_layout.addWidget(self.rgb_label)
        info_layout.addWidget(self.hsv_label)
        layout.addLayout(info_layout)

    def refresh_theme_styles(self):
        app = QApplication.instance()
        pal = app.palette() if app else QPalette()
        bg_window = pal.color(QPalette.ColorRole.Window).name()
        text_main = pal.color(QPalette.ColorRole.WindowText).name()
        border_col = pal.color(QPalette.ColorRole.Mid).name()

        self.setStyleSheet(f"background-color: {bg_window}; border-radius: 8px;")
        self.card.setStyleSheet(f"""
            QFrame#ColorCard {{
                background-color: {bg_window};
                color: {text_main};
                border: 1px solid {border_col};
                border-radius: 8px;
            }}
            QLabel {{
                color: {text_main};
            }}
        """)

    def update_color(self, curr_color, prev_color):
        if not curr_color or not curr_color.isValid():
            return
        
        self.swatch.setColors(curr_color, prev_color or curr_color)

        hex_str = curr_color.name().upper()
        self.hex_label.setText(hex_str)

        r, g, b = curr_color.red(), curr_color.green(), curr_color.blue()
        self.rgb_label.setText(f"RGB: {r}, {g}, {b}")

        h, s, v, _ = curr_color.getHsv()
        if h < 0: h = 0
        s_pct = int((s / 255.0) * 100)
        v_pct = int((v / 255.0) * 100)
        self.hsv_label.setText(f"HSV: {h}°, {s_pct}%, {v_pct}%")

        self.card.update()
        self.update()

    def popup_at(self, docker_widget=None):
        if self.isVisible():
            self.card.update()
            self.update()
            self.raise_()
            return

        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

        if docker_widget and docker_widget.isVisible():
            d_left = docker_widget.mapToGlobal(QPoint(0, 0)).x()
            d_right = docker_widget.mapToGlobal(QPoint(docker_widget.width(), 0)).x()
            d_top = docker_widget.mapToGlobal(QPoint(0, 0)).y()
            d_height = docker_widget.height()

            if d_left - geo.left() >= self.width() + 10:
                x = d_left - self.width() - 8
            elif geo.right() - d_right >= self.width() + 10:
                x = d_right + 8
            else:
                x = d_left + 16

            y = d_top + (d_height - self.height()) // 2
            if y + self.height() > geo.bottom():
                y = geo.bottom() - self.height() - 8
            if y < geo.top():
                y = geo.top() + 8
        else:
            pos = QCursor.pos()
            x = pos.x() + 16
            y = pos.y() - 50

        self.move(x, y)
        self.show()
        self.raise_()
        self.card.update()
        self.update()


class SettingsDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("设置 (Settings)")
        self.config = config or {"mode": "v-hsv", "hue_style": "slider", "show_preview": True, "history_pos": "bottom"}
        
        layout = QVBoxLayout()
        
        mode_group = QGroupBox("色彩模型 (Color Model)")
        mode_layout = QVBoxLayout()
        self.radio_hsv = QRadioButton("标准 HSV (Krita/PS 默认)")
        self.radio_vhsv = QRadioButton("V-HSV (SAI 强力鲜艳暗部)")
        if self.config["mode"] == "hsv": self.radio_hsv.setChecked(True)
        else: self.radio_vhsv.setChecked(True)
        mode_layout.addWidget(self.radio_hsv)
        mode_layout.addWidget(self.radio_vhsv)
        mode_group.setLayout(mode_layout)
        
        hue_group = QGroupBox("色相选择器 (Hue Selector)")
        hue_layout = QVBoxLayout()
        self.radio_slider = QRadioButton("垂直滑块 (Vertical Slider)")
        self.radio_ring = QRadioButton("色相环 (Hue Ring)")
        if self.config["hue_style"] == "ring": self.radio_ring.setChecked(True)
        else: self.radio_slider.setChecked(True)
        hue_layout.addWidget(self.radio_slider)
        hue_layout.addWidget(self.radio_ring)
        hue_group.setLayout(hue_layout)
        
        extra_group = QGroupBox("界面与历史 (UI & History)")
        extra_layout = QFormLayout()
        
        self.chk_preview = QCheckBox("显示光标跟随预览窗 (Cursor Preview)")
        self.chk_preview.setChecked(self.config.get("show_preview", True))
        
        self.combo_history = QComboBox()
        self.combo_history.addItems(["无 (None)", "上方 (Top)", "下方 (Bottom)", "左侧 (Left)", "右侧 (Right)"])
        mapping = {"none": 0, "top": 1, "bottom": 2, "left": 3, "right": 4}
        self.combo_history.setCurrentIndex(mapping.get(self.config.get("history_pos", "bottom"), 2))
        
        extra_layout.addRow(self.chk_preview)
        extra_layout.addRow("历史记录:", self.combo_history)
        extra_group.setLayout(extra_layout)
        
        btn_apply = QPushButton("确定 (Apply)")
        btn_apply.clicked.connect(self.accept)
        
        layout.addWidget(mode_group)
        layout.addWidget(hue_group)
        layout.addWidget(extra_group)
        layout.addWidget(btn_apply)
        self.setLayout(layout)
        
    def get_config(self):
        inv_mapping = {0: "none", 1: "top", 2: "bottom", 3: "left", 4: "right"}
        return {
            "mode": "hsv" if self.radio_hsv.isChecked() else "v-hsv",
            "hue_style": "ring" if self.radio_ring.isChecked() else "slider",
            "show_preview": self.chk_preview.isChecked(),
            "history_pos": inv_mapping[self.combo_history.currentIndex()]
        }


class ColorHistory(QWidget):
    colorSelected = pyqtSignal(QColor)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = [QColor(240, 240, 240)] * 60
        self.expanded = False
        self.orientation = "horizontal"
        
    def setOrientation(self, orientation):
        self.orientation = orientation
        self.update()
            
    def addColor(self, c):
        if not c: return
        if self.colors[0].rgb() == c.rgb(): return
        self.colors.insert(0, QColor(c))
        if len(self.colors) > 60:
            self.colors = self.colors[:60]
        self.update()
        
    def collapse(self):
        if self.expanded:
            self.expanded = False
            if self.parent():
                self.parent().updateLayout()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        
        if self.orientation == "horizontal":
            display_count = max(1, w // 20)
        else:
            display_count = max(1, h // 20)
            
        max_colors = display_count * 3
        count = max_colors if self.expanded else display_count
        count = min(count, len(self.colors))
        
        painter.setRenderHint(RenderHint_Antialiasing)
        
        for i in range(count):
            if self.orientation == "horizontal":
                col = i % display_count
                row = i // display_count
                rect = QRectF(col * 20, row * 20, 20, 20)
            else:
                if self.expanded:
                    row = i % display_count
                    col = i // display_count
                    rect = QRectF(col * 20, row * 20, 20, 20)
                else:
                    rect = QRectF(0, i * 20, 20, 20)
                
            if not self.expanded and i == display_count - 1:
                # Draw sleek button
                painter.setBrush(QBrush(QColor(60, 60, 60), BrushStyle_SolidPattern))
                painter.setPen(QPen(QColor(30, 30, 30), 1))
                painter.drawRect(rect)
                
                painter.setBrush(QBrush(QColor(200, 200, 200), BrushStyle_SolidPattern))
                painter.setPen(QPen(Color_transparent))
                
                cx = rect.x() + 10
                cy = rect.y() + 10
                
                poly = QPolygonF()
                if self.orientation == "horizontal":
                    poly.append(QPointF(cx - 4, cy - 2))
                    poly.append(QPointF(cx + 4, cy - 2))
                    poly.append(QPointF(cx, cy + 4))
                else:
                    poly.append(QPointF(cx - 2, cy - 4))
                    poly.append(QPointF(cx - 2, cy + 4))
                    poly.append(QPointF(cx + 4, cy))
                    
                painter.drawPolygon(poly)
            else:
                painter.setBrush(QBrush(self.colors[i], BrushStyle_SolidPattern))
                painter.setPen(QPen(Color_black, 1))
                painter.drawRect(rect)
                
    def mousePressEvent(self, event):
        if event.button() == RightButton:
            event.ignore()
            return
            
        pos = event.pos()
        w = self.width()
        h = self.height()
        
        if self.orientation == "horizontal":
            display_count = max(1, w // 20)
            col = int(pos.x() // 20)
            row = int(pos.y() // 20)
            idx = row * display_count + col
        else:
            display_count = max(1, h // 20)
            row = int(pos.y() // 20)
            col = int(pos.x() // 20)
            idx = col * display_count + row
            
        max_colors = display_count * 3
        count = max_colors if self.expanded else display_count
        count = min(count, len(self.colors))
        
        if 0 <= idx < count:
            if not self.expanded and idx == display_count - 1:
                self.expanded = True
                if self.parent(): self.parent().updateLayout()
            else:
                self.collapse()
                self.colorSelected.emit(self.colors[idx])
        else:
            self.collapse()


class SVSquare(QWidget):
    colorSelected = pyqtSignal(QColor)
    pickingStarted = pyqtSignal()
    pickingEnded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hue = 0.0
        self.s = 0.0
        self.v = 1.0
        self.mode = "v-hsv"
        self.show_preview = True
        self.res = 64
        self._image = QImage(self.res, self.res, ImageFormat_RGB32)
        
        self.is_picking = False
        self.previous_color = QColor(Color_white)
        self.current_color = QColor(Color_white)
        self._last_rendered_hue = -1
        self._last_rendered_mode = ""
        self.updateImage()

    def forceUpdateImage(self):
        self.updateImage(force=True)
        self.update()

    def setHue(self, hue):
        if self.hue == hue: return
        self.hue = hue
        
        # Always emit color instantly to keep preview UI smooth
        self.emitColor()
        
        # Throttle expensive background calculation to 30fps when sliding hue fast
        import time
        now = time.time()
        if not hasattr(self, "_last_image_update"): self._last_image_update = 0
        
        is_hue_picking = getattr(self.parent(), "hue", None) and getattr(self.parent().hue, "is_picking", False)
        
        if is_hue_picking:
            if now - self._last_image_update < 0.033:
                return
                
        self._last_image_update = now
        self.updateImage()
        self.update()
        
    def setMode(self, mode):
        self.mode = mode
        self.updateImage(force=True)
        self.update()
        self.emitColor()

    def updateImage(self, force=False):
        int_hue = int(self.hue)
        if not force and self._last_rendered_hue == int_hue and self._last_rendered_mode == self.mode:
            return
            
        self._last_rendered_hue = int_hue
        self._last_rendered_mode = self.mode
        
        hp = int_hue / 60.0
        
        for x in range(self.res):
            s = x / float(self.res - 1)
            for y in range(self.res):
                val_y = 1.0 - (y / float(self.res - 1))
                
                if self.mode == "v-hsv":
                    s_adj = math.pow(s, (val_y + 0.5) / 1.5) if s > 0 else 0.0
                    c = val_y * s_adj
                    m = val_y - c
                    x_val = c * (1 - abs(hp % 2 - 1))
                elif self.mode == "hsl":
                    c = (1.0 - abs(2.0 * val_y - 1.0)) * s
                    x_val = c * (1 - abs(hp % 2 - 1))
                    m = val_y - c / 2.0
                elif self.mode == "hsy":
                    c = val_y * s
                    x_val = c * (1 - abs(hp % 2 - 1))
                    m = val_y - (0.299 * c + 0.587 * x_val)
                else: # hsv
                    c = val_y * s
                    x_val = c * (1 - abs(hp % 2 - 1))
                    m = val_y - c
                    
                if hp < 1: r,g,b = c, x_val, 0
                elif hp < 2: r,g,b = x_val, c, 0
                elif hp < 3: r,g,b = 0, c, x_val
                elif hp < 4: r,g,b = 0, x_val, c
                elif hp < 5: r,g,b = x_val, 0, c
                else: r,g,b = c, 0, x_val
                
                R = max(0, min(255, int((r+m)*255)))
                G = max(0, min(255, int((g+m)*255)))
                B = max(0, min(255, int((b+m)*255)))
                
                self._image.setPixel(x, y, (R<<16) | (G<<8) | B)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(RenderHint_SmoothPixmapTransform)
        painter.setRenderHint(RenderHint_Antialiasing)
        painter.drawImage(self.rect(), self._image)

        w = float(self.width())
        h = float(self.height())

        # 绘制色域遮罩 (Gamut Masking)
        gamut_mask = getattr(self, 'gamut_mask', 'None')
        if gamut_mask != "None":
            mask_path = QPainterPath()
            mask_path.addRect(QRectF(0, 0, w, h))

            cut_path = QPainterPath()
            if gamut_mask == "Triad":
                poly = QPolygonF([
                    QPointF(w * 0.1, h * 0.1),
                    QPointF(w * 0.9, h * 0.1),
                    QPointF(w * 0.5, h * 0.9)
                ])
                cut_path.addPolygon(poly)
            elif gamut_mask == "Dominant":
                poly = QPolygonF([
                    QPointF(w * 0.1, h * 0.9),
                    QPointF(w * 0.9, h * 0.1),
                    QPointF(w * 0.9, h * 0.9)
                ])
                cut_path.addPolygon(poly)
            elif gamut_mask == "Sunset":
                poly = QPolygonF([
                    QPointF(w * 0.15, h * 0.15),
                    QPointF(w * 0.85, h * 0.35),
                    QPointF(w * 0.65, h * 0.9),
                    QPointF(w * 0.15, h * 0.85)
                ])
                cut_path.addPolygon(poly)
            elif gamut_mask == "Atmosphere":
                poly = QPolygonF([
                    QPointF(w * 0.5, h * 0.1),
                    QPointF(w * 0.85, h * 0.5),
                    QPointF(w * 0.5, h * 0.9),
                    QPointF(w * 0.15, h * 0.5)
                ])
                cut_path.addPolygon(poly)
            elif gamut_mask == "Complementary":
                cut_path.addRect(QRectF(w * 0.1, 0, w * 0.3, h))
                cut_path.addRect(QRectF(w * 0.6, 0, w * 0.3, h))
            elif gamut_mask == "Muted":
                cut_path.addRect(QRectF(w * 0.05, h * 0.1, w * 0.45, h * 0.8))

            mask_path = mask_path.subtracted(cut_path)
            painter.setPen(QPen(Color_transparent))
            painter.setBrush(QBrush(QColor(0, 0, 0, 135)))
            painter.drawPath(mask_path)

        cursor_x = int(self.s * self.width())
        cursor_y = int((1.0 - self.v) * self.height())
        painter.setPen(QPen(Color_white, 1))
        painter.drawEllipse(QPointF(cursor_x, cursor_y), 4, 4)
        painter.setPen(QPen(Color_black, 1))
        painter.drawEllipse(QPointF(cursor_x, cursor_y), 5, 5)

    def mousePressEvent(self, event):
        if event.button() == RightButton:
            event.ignore()
            return
        self.is_picking = True
        if Krita.instance().activeWindow() and Krita.instance().activeWindow().activeView():
            fg = Krita.instance().activeWindow().activeView().foregroundColor()
            self.previous_color = fg.colorForCanvas(Krita.instance().activeWindow().activeView().canvas())
        else:
            self.previous_color = self.current_color
            
        self.locked_s_val = self.s
        self.locked_v_val = self.v
        self.pickingStarted.emit()
        self.updateValue(event.pos())

    def mouseMoveEvent(self, event):
        self.updateValue(event.pos())
        
    def mouseReleaseEvent(self, event):
        if event.button() == RightButton:
            return
        self.is_picking = False
        if hasattr(self, 'docker') and self.docker:
            self.docker.hide_color_preview()
        self.pickingEnded.emit()
        self.update()

    def _clamp_to_gamut(self, s, v):
        gamut_mask = getattr(self, 'gamut_mask', 'None')
        if gamut_mask == "None":
            return s, v

        y = 1.0 - v
        if gamut_mask == "Triad":
            y = max(0.1, min(0.9, y))
            t = (0.9 - y) / 0.8
            min_s = 0.5 - 0.4 * t
            max_s = 0.5 + 0.4 * t
            s = max(min_s, min(max_s, s))
            v = 1.0 - y
        elif gamut_mask == "Dominant":
            y = max(0.1, min(0.9, y))
            min_s = 0.1 + 0.8 * (y - 0.1) / 0.8
            max_s = 0.9
            s = max(min_s, min(max_s, s))
            v = 1.0 - y
        elif gamut_mask == "Sunset":
            y = max(0.15, min(0.9, y))
            t = (y - 0.15) / 0.75
            min_s = 0.15
            max_s = 0.85 - 0.2 * t
            s = max(min_s, min(max_s, s))
            v = 1.0 - y
        elif gamut_mask == "Atmosphere":
            y = max(0.1, min(0.9, y))
            dist_y = abs(y - 0.5) / 0.4
            half_w = 0.35 * (1.0 - dist_y)
            min_s = 0.5 - half_w
            max_s = 0.5 + half_w
            s = max(min_s, min(max_s, s))
            v = 1.0 - y
        elif gamut_mask == "Complementary":
            s = max(0.1, min(0.9, s))
            if 0.4 < s < 0.5: s = 0.4
            elif 0.5 <= s < 0.6: s = 0.6
        elif gamut_mask == "Muted":
            s = max(0.05, min(0.5, s))
            v = max(0.1, min(0.9, v))

        return s, v

    def updateValue(self, pos):
        w = max(1.0, float(self.width()))
        h = max(1.0, float(self.height()))
        x = max(0.0, min(w, float(pos.x())))
        y = max(0.0, min(h, float(pos.y())))

        new_s = x / w
        new_v = 1.0 - (y / h)

        if getattr(self, 'lock_s', False) and hasattr(self, 'locked_s_val'):
            new_s = self.locked_s_val
        if getattr(self, 'lock_v', False) and hasattr(self, 'locked_v_val'):
            new_v = self.locked_v_val

        new_s, new_v = self._clamp_to_gamut(new_s, new_v)

        self.s = new_s
        self.v = new_v
        self.update()
        self.emitColor()
        if self.is_picking and hasattr(self, 'docker') and self.docker:
            self.docker.show_color_preview(self.current_color, self.previous_color)
        
    def emitColor(self):
        hp = self.hue / 60.0
        
        if self.mode == "v-hsv":
            s_adj = math.pow(self.s, (self.v + 0.5) / 1.5) if self.s > 0 else 0.0
            c = self.v * s_adj
            m = self.v - c
            x_val = c * (1 - abs(hp % 2 - 1))
        elif self.mode == "hsl":
            c = (1.0 - abs(2.0 * self.v - 1.0)) * self.s
            x_val = c * (1 - abs(hp % 2 - 1))
            m = self.v - c / 2.0
        elif self.mode == "hsy":
            c = self.v * self.s
            x_val = c * (1 - abs(hp % 2 - 1))
            m = self.v - (0.299 * c + 0.587 * x_val)
        else:
            c = self.v * self.s
            m = self.v - c
            x_val = c * (1 - abs(hp % 2 - 1))
            
        if hp < 1: r,g,b = c, x_val, 0
        elif hp < 2: r,g,b = x_val, c, 0
        elif hp < 3: r,g,b = 0, c, x_val
        elif hp < 4: r,g,b = 0, x_val, c
        elif hp < 5: r,g,b = x_val, 0, c
        else: r,g,b = c, 0, x_val
        
        R = max(0, min(255, int((r+m)*255)))
        G = max(0, min(255, int((g+m)*255)))
        B = max(0, min(255, int((b+m)*255)))
        
        color = QColor(R, G, B)
        self.current_color = color
        
        docker = self.parent().parent() if hasattr(self.parent(), "parent") else None
        if docker and hasattr(docker, "last_color"):
            docker.last_color = color
            
        self.colorSelected.emit(color)


class HueSelector(QWidget):
    hueChanged = pyqtSignal(float)
    pickingStarted = pyqtSignal()
    pickingEnded = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.style = "slider"
        self.hue = 0.0
        self.is_picking = False
        self._image_slider = QImage(1, 360, ImageFormat_RGB32)
        for y in range(360):
            color = QColor()
            color.setHsv(359 - y, 255, 255)
            self._image_slider.setPixel(0, y, color.rgb())

    def setStyle(self, style):
        self.style = style
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(RenderHint_SmoothPixmapTransform)
        
        if self.style == "slider":
            painter.drawImage(self.rect(), self._image_slider)
            y = int((1.0 - self.hue / 360.0) * self.height())
            y = max(0, min(self.height() - 1, y))
            painter.setPen(QPen(Color_black, 2))
            painter.drawLine(0, y, self.width(), y)
            painter.setPen(QPen(Color_white, 1))
            painter.drawLine(0, y, self.width(), y)
        else:
            w = self.width()
            h = self.height()
            center = QPointF(w / 2.0, h / 2.0)
            radius = min(w, h) / 2.0 - 5
            ring_width = 15
            
            painter.setRenderHint(RenderHint_Antialiasing)
            
            gradient = QConicalGradient(center, 150)
            gradient.setColorAt(0.0, QColor(255, 0, 0))
            gradient.setColorAt(60/360.0, QColor(255, 0, 255))
            gradient.setColorAt(120/360.0, QColor(0, 0, 255))
            gradient.setColorAt(180/360.0, QColor(0, 255, 255))
            gradient.setColorAt(240/360.0, QColor(0, 255, 0))
            gradient.setColorAt(300/360.0, QColor(255, 255, 0))
            gradient.setColorAt(1.0, QColor(255, 0, 0))
            
            stroke_radius = radius - ring_width / 2.0
            rect = QRectF(center.x() - stroke_radius, center.y() - stroke_radius, stroke_radius * 2, stroke_radius * 2)
            
            pen = QPen(QBrush(gradient), ring_width)
            painter.setPen(pen)
            painter.drawEllipse(rect)
            
            rad = math.radians(150 - self.hue)
            cx = center.x() + stroke_radius * math.cos(rad)
            cy = center.y() - stroke_radius * math.sin(rad)
            
            painter.setPen(QPen(Color_white, 2))
            painter.drawEllipse(QPointF(cx, cy), 4, 4)
            painter.setPen(QPen(Color_black, 1))
            painter.drawEllipse(QPointF(cx, cy), 5, 5)

    def mousePressEvent(self, event):
        if event.button() == RightButton:
            event.ignore()
            return
        self.is_picking = True
        self.pickingStarted.emit()
        self.updateHue(event.pos())
        if hasattr(self, 'docker') and self.docker and hasattr(self.docker, 'sv_square'):
            self.docker.show_color_preview(self.docker.sv_square.current_color, self.docker.sv_square.previous_color)

    def mouseReleaseEvent(self, event):
        if event.button() == RightButton:
            return
        self.is_picking = False
        if hasattr(self, 'docker') and self.docker:
            self.docker.hide_color_preview()
        self.pickingEnded.emit()
        
    def mouseMoveEvent(self, event):
        self.updateHue(event.pos())

    def updateHue(self, pos):
        if self.style == "slider":
            y = max(0, min(self.height(), pos.y()))
            new_hue = (1.0 - (y / self.height())) * 360.0
        else:
            w = self.width()
            h = self.height()
            dx = pos.x() - w / 2.0
            dy = h / 2.0 - pos.y()
            angle = math.degrees(math.atan2(dy, dx))
            new_hue = 150 - angle
            if new_hue < 0: new_hue += 360.0
            new_hue = new_hue % 360.0
            
        if self.hue != new_hue:
            self.hue = new_hue
            self.hueChanged.emit(self.hue)
            self.update()
        if self.is_picking and hasattr(self, 'docker') and self.docker and hasattr(self.docker, 'sv_square'):
            self.docker.show_color_preview(self.docker.sv_square.current_color, self.docker.sv_square.previous_color)


class PickerContainer(QWidget):
    def __init__(self, sv, hue, history):
        super().__init__()
        self.sv = sv
        self.hue = hue
        self.history = history
        self.style = "slider"
        self.history_pos = "bottom"
        
        self.hue.setParent(self)
        self.sv.setParent(self)
        self.history.setParent(self)
        
    def setConfig(self, style, history_pos):
        self.style = style
        self.history_pos = history_pos
        self.hue.setStyle(style)
        self.updateLayout()
        
    def resizeEvent(self, event):
        self.updateLayout()
        
    def updateLayout(self):
        w = self.width()
        h = self.height()
        if w == 0 or h == 0: return
        
        px, py, pw, ph = 0, 0, w, h
        hist_size = 20
        
        if self.history_pos == "top":
            py += hist_size; ph -= hist_size
        elif self.history_pos == "bottom":
            ph -= hist_size
        elif self.history_pos == "left":
            px += hist_size; pw -= hist_size
        elif self.history_pos == "right":
            pw -= hist_size
            
        if self.style == "slider":
            self.sv.setGeometry(px, py, pw - 25, ph)
            self.hue.setGeometry(px + pw - 20, py, 20, ph)
        else:
            size = min(pw, ph)
            x_offset = px + (pw - size) // 2
            y_offset = py + (ph - size) // 2
            
            self.hue.setGeometry(x_offset, y_offset, size, size)
            
            inner_radius = size / 2.0 - 20
            sq_size = int((inner_radius * 2) * 0.707) - 2
            sq_x = x_offset + (size - sq_size) // 2
            sq_y = y_offset + (size - sq_size) // 2
            
            self.sv.setGeometry(int(sq_x), int(sq_y), int(sq_size), int(sq_size))
            
        self.sv.raise_()
                
        if self.history_pos != "none":
            self.history.show()
            box_size = 20
            
            if self.history.orientation == "horizontal":
                display_count = max(1, w // 20)
                hist_w = w
                hist_h = box_size
                hist_x = 0
                
                if not self.history.expanded:
                    if self.history_pos == "top": self.history.setGeometry(hist_x, 0, hist_w, hist_h)
                    else: self.history.setGeometry(hist_x, h - hist_h, hist_w, hist_h)
                else:
                    total_colors = len(self.history.colors)
                    cols = display_count
                    rows = min(3, (total_colors - 1) // cols + 1)
                    exp_h = rows * box_size
                    if self.history_pos == "top": self.history.setGeometry(hist_x, 0, hist_w, exp_h)
                    else: self.history.setGeometry(hist_x, h - exp_h, hist_w, exp_h)
            else:
                display_count = max(1, h // 20)
                hist_w = box_size
                hist_h = h
                hist_y = 0
                
                if not self.history.expanded:
                    if self.history_pos == "left": self.history.setGeometry(0, hist_y, hist_w, hist_h)
                    else: self.history.setGeometry(w - hist_w, hist_y, hist_w, hist_h)
                else:
                    total_colors = len(self.history.colors)
                    rows = display_count
                    cols = min(3, (total_colors - 1) // rows + 1)
                    exp_w = cols * box_size
                    if self.history_pos == "left": self.history.setGeometry(0, hist_y, exp_w, hist_h)
                    else: self.history.setGeometry(w - exp_w, hist_y, exp_w, hist_h)
            
            self.history.raise_()
        else:
            self.history.hide()


class AdvancedToolBar(QWidget):
    """Pigment.O 灵感高阶工具栏：色域遮罩列表、色彩空间列表 (QMenu 下拉菜单模式)"""
    def __init__(self, docker, parent=None):
        super().__init__(parent)
        self.docker = docker
        self.setFixedHeight(28)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        app = QApplication.instance()
        pal = app.palette() if app else QPalette()
        self.icon_col = pal.color(QPalette.ColorRole.WindowText).name()

        # 1. 色域遮罩 QMenu 下拉列表
        self.btn_gamut = QToolButton(self)
        self.btn_gamut.setText(" Mask: Off")
        self.btn_gamut.setIcon(get_lucide_icon("shield", color=self.icon_col, size=14))
        self.btn_gamut.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_gamut.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_gamut.setToolTip("选择色域遮罩限域 (Gamut Masking)")
        
        self.gamut_menu = QMenu(self)
        self.btn_gamut.setMenu(self.gamut_menu)
        self._build_gamut_menu()

        # 2. 色彩空间 QMenu 下拉列表
        self.btn_space = QToolButton(self)
        self.btn_space.setText(" Space: v-HSV")
        self.btn_space.setIcon(get_lucide_icon("sliders", color=self.icon_col, size=14))
        self.btn_space.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_space.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_space.setToolTip("选择色彩空间 (v-HSV / HSV / HSL / HSY')")
        
        self.space_menu = QMenu(self)
        self.btn_space.setMenu(self.space_menu)
        self._build_space_menu()

        layout.addWidget(self.btn_gamut)
        layout.addStretch(1)
        layout.addWidget(self.btn_space)

        self.refresh_styles()

    def _build_gamut_menu(self):
        self.gamut_menu.clear()
        masks = [
            ("None", "无遮罩 (Off)"),
            ("Triad", "正三角形 (Triad)"),
            ("Dominant", "主色高光 (Dominant)"),
            ("Sunset", "暖夕阳 (Sunset)"),
            ("Atmosphere", "大气高雾 (Atmosphere)"),
            ("Complementary", "双极补色 (Complementary)"),
            ("Muted", "低饱和灰度 (Muted)")
        ]
        curr = getattr(self.docker.sv_square, 'gamut_mask', "None")
        for key, label in masks:
            act = self.gamut_menu.addAction(label)
            act.setCheckable(True)
            if key == curr:
                act.setChecked(True)
            act.triggered.connect(lambda _, k=key, l=label: self._set_gamut(k, l))

    def _set_gamut(self, key, label):
        self.docker.sv_square.gamut_mask = key
        self.docker.sv_square.update()
        short_label = key if key != "None" else "Off"
        self.btn_gamut.setText(f" Mask: {short_label}")
        self._build_gamut_menu()

    def _build_space_menu(self):
        self.space_menu.clear()
        spaces = [
            ("v-hsv", "v-HSV (PaintTool SAI 视角)"),
            ("hsv", "HSV (标准 HSV)"),
            ("hsl", "HSL (Lightness 亮度模型)"),
            ("hsy", "HSY' (Perceptual Luma 感知明度)")
        ]
        curr = self.docker.config.get("mode", "v-hsv")
        for key, label in spaces:
            act = self.space_menu.addAction(label)
            act.setCheckable(True)
            if key == curr:
                act.setChecked(True)
            act.triggered.connect(lambda _, k=key: self._set_space(k))

    def _set_space(self, key):
        labels = {"v-hsv": "v-HSV", "hsv": "HSV", "hsl": "HSL", "hsy": "HSY'"}
        self.docker.config["mode"] = key
        self.docker.applyConfig()
        self.btn_space.setText(f" Space: {labels.get(key, key)}")
        self._build_space_menu()

    def refresh_styles(self):
        app = QApplication.instance()
        pal = app.palette() if app else QPalette()
        text_main = pal.color(QPalette.ColorRole.WindowText).name()
        border_col = pal.color(QPalette.ColorRole.Mid).name()
        bg_win = pal.color(QPalette.ColorRole.Window).name()
        self.icon_col = text_main

        qss = f"""
            QToolButton {{
                background-color: transparent;
                color: {text_main};
                border: 1px solid {border_col};
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
                font-weight: 500;
            }}
            QToolButton::menu-indicator {{
                image: none;
                width: 0px;
            }}
            QToolButton:hover {{
                background-color: rgba(128, 128, 128, 0.2);
            }}
            QMenu {{
                background-color: {bg_win};
                color: {text_main};
                border: 1px solid {border_col};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 4px 20px 4px 10px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: rgba(120, 140, 200, 0.35);
            }}
        """
        self.setStyleSheet(qss)


class VhsvDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Color Picker")
        self.config = {"mode": "v-hsv", "hue_style": "slider", "show_preview": True, "history_pos": "bottom"}
        
        try:
            saved = Krita.instance().readSetting("sai_vhsv_picker", "config", "")
            if saved:
                loaded = json.loads(saved)
                self.config.update(loaded)
        except Exception:
            pass
            
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(2)
        
        self.sv_square = SVSquare()
        self.hue_selector = HueSelector()
        self.history = ColorHistory()
        
        self.color_preview = ColorPreviewPopup(self)
        self.color_preview.hide()
        self.sv_square.docker = self
        self.hue_selector.docker = self
        
        if "history" in self.config:
            hist_colors = [QColor(h) for h in self.config["history"]]
            while len(hist_colors) < 60: hist_colors.append(QColor(240, 240, 240))
            self.history.colors = hist_colors[:60]
        
        self.picker_container = PickerContainer(self.sv_square, self.hue_selector, self.history)
        self.toolbar = AdvancedToolBar(self)

        self.main_layout.addWidget(self.picker_container, 1)
        self.main_layout.addWidget(self.toolbar)

        self.main_widget.setLayout(self.main_layout)
        self.setWidget(self.main_widget)
        
        self.hue_selector.hueChanged.connect(self.sv_square.setHue)
        self.hue_selector.pickingStarted.connect(self.onPickingStarted)
        self.hue_selector.pickingEnded.connect(self.sv_square.forceUpdateImage)
        self.sv_square.colorSelected.connect(self.onColorSelected)
        self.sv_square.pickingStarted.connect(self.onPickingStarted)
        self.sv_square.pickingEnded.connect(self.onPickingEnded)
        self.history.colorSelected.connect(self.onHistorySelected)

        self.applyConfig()
        
        self.last_color = QColor()
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.checkKritaColor)
        self.timer.start()

    def show_color_preview(self, current_color, previous_color):
        if self.config.get("show_preview", True):
            if hasattr(self, '_hide_timer'):
                self._hide_timer.stop()
            self.color_preview.update_color(current_color, previous_color)
            self.color_preview.popup_at(docker_widget=self)

    def hide_color_preview(self):
        if hasattr(self, '_hide_timer'):
            self._hide_timer.stop()
        if hasattr(self, 'color_preview') and self.color_preview:
            self.color_preview.hide()

    def showEvent(self, event):
        super().showEvent(event)
        self.applyConfig()
        if hasattr(self, 'picker_container') and self.picker_container:
            self.picker_container.updateLayout()
        

    def checkKritaColor(self):
        if not Krita.instance().activeWindow(): return
        view = Krita.instance().activeWindow().activeView()
        if not view: return
        
        try:
            qcolor = view.foregroundColor().colorForCanvas(view.canvas())
            
            if qcolor != self.last_color:
                self.last_color = qcolor

                if hasattr(self, '_internal_pick_color') and self._internal_pick_color == qcolor:
                    del self._internal_pick_color
                    return
                
                if not self.sv_square.is_picking and not self.hue_selector.is_picking:
                    mode = self.sv_square.mode
                    if mode == "hsl":
                        h, s, l, a = qcolor.getHslF()
                        if h >= 0:
                            hue = h * 360.0
                            self.hue_selector.hue = hue
                            self.sv_square.hue = hue
                        self.sv_square.s = s
                        self.sv_square.v = l
                    elif mode == "hsy":
                        h, s, v, a = qcolor.getHsvF()
                        if h >= 0:
                            hue = h * 360.0
                            self.hue_selector.hue = hue
                            self.sv_square.hue = hue
                        r, g, b = qcolor.redF(), qcolor.greenF(), qcolor.blueF()
                        y = 0.299 * r + 0.587 * g + 0.114 * b
                        max_rgb = max(r, g, b)
                        min_rgb = min(r, g, b)
                        s_hsy = (max_rgb - min_rgb) / max_rgb if max_rgb > 0 else 0.0
                        self.sv_square.s = s_hsy
                        self.sv_square.v = y
                    elif mode == "v-hsv":
                        h, s, v, a = qcolor.getHsvF()
                        if h >= 0:
                            hue = h * 360.0
                            self.hue_selector.hue = hue
                            self.sv_square.hue = hue
                        self.sv_square.v = v
                        if v == 0:
                            self.sv_square.s = 0.0
                        else:
                            import math
                            self.sv_square.s = math.pow(s, 1.5 / (v + 0.5))
                    else: # hsv
                        h, s, v, a = qcolor.getHsvF()
                        if h >= 0:
                            hue = h * 360.0
                            self.hue_selector.hue = hue
                            self.sv_square.hue = hue
                        self.sv_square.s = s
                        self.sv_square.v = v
                        
                    self.hue_selector.update()
                    self.sv_square.current_color = qcolor
                    self.sv_square.updateImage(force=True)
                    self.sv_square.update()
        except Exception:
            pass

    def saveConfig(self):
        try:
            cfg = self.config.copy()
            cfg["history"] = [c.name() for c in self.history.colors if c.name() != "#f0f0f0"]
            Krita.instance().writeSetting("sai_vhsv_picker", "config", json.dumps(cfg))
        except Exception:
            pass
        
    def applyConfig(self):
        self.sv_square.setMode(self.config["mode"])
        self.sv_square.show_preview = self.config.get("show_preview", True)
        
        pos = self.config["history_pos"]
        if pos in ["left", "right"]:
            self.history.setOrientation("vertical")
        else:
            self.history.setOrientation("horizontal")
            
        self.picker_container.setConfig(self.config["hue_style"], self.config["history_pos"])
        self.saveConfig()
            
    def contextMenuEvent(self, event):
        self.openSettings()
        
    def openSettings(self):
        dlg = SettingsDialog(self, self.config)
        if hasattr(dlg, 'exec'):
            res = dlg.exec()
        else:
            res = dlg.exec_()
            
        if res:
            self.config = dlg.get_config()
            self.applyConfig()

    def onPickingStarted(self):
        self.history.collapse()

    def onPickingEnded(self):
        self.history.addColor(self.sv_square.current_color)
        self.saveConfig()

    def onColorSelected(self, qcolor):
        if not Krita.instance().activeWindow(): return
        view = Krita.instance().activeWindow().activeView()
        if not view: return
        
        import time
        if not hasattr(self, "_last_fg_update"): self._last_fg_update = 0
        now = time.time()
        
        # If still picking and it's been less than 33ms, drop update to prevent lag
        if getattr(self.sv_square, "is_picking", False) or getattr(self.hue_selector, "is_picking", False):
            if now - self._last_fg_update < 0.033:
                return
                
        self._last_fg_update = now
        self._internal_pick_color = qcolor
        
        try:
            ko_color = ManagedColor.fromQColor(qcolor)
            view.setForeGroundColor(ko_color)
        except Exception as e:
            pass
            
    def onHistorySelected(self, qcolor):
        if not Krita.instance().activeWindow(): return
        view = Krita.instance().activeWindow().activeView()
        if not view: return
        
        try:
            ko_color = ManagedColor.fromQColor(qcolor)
            view.setForeGroundColor(ko_color)
        except Exception as e:
            pass

    def canvasChanged(self, canvas):
        pass
