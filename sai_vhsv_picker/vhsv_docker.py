import math
import json
from krita import *
from .qt_compat import *

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
                v = 1.0 - (y / float(self.res - 1))
                
                if self.mode == "v-hsv":
                    s_adj = math.pow(s, (v + 0.5) / 1.5) if s > 0 else 0.0
                    c = v * s_adj
                else:
                    c = v * s
                    
                x_val = c * (1 - abs(hp % 2 - 1))
                m = v - c
                
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
        painter.drawImage(self.rect(), self._image)
        
        cursor_x = int(self.s * self.width())
        cursor_y = int((1.0 - self.v) * self.height())
        painter.setPen(QPen(Color_white, 1))
        painter.drawEllipse(QPointF(cursor_x, cursor_y), 4, 4)
        painter.setPen(QPen(Color_black, 1))
        painter.drawEllipse(QPointF(cursor_x, cursor_y), 5, 5)
        
        if self.is_picking and self.show_preview:
            popup_x = cursor_x + 15
            popup_y = cursor_y - 30
            if popup_x > self.width() - 40: popup_x = cursor_x - 40
            if popup_y < 0: popup_y = cursor_y + 15
            
            painter.setPen(QPen(Color_black, 1))
            painter.fillRect(popup_x, popup_y, 30, 15, self.current_color)
            painter.drawRect(popup_x, popup_y, 30, 15)
            painter.fillRect(popup_x, popup_y + 15, 30, 15, self.previous_color)
            painter.drawRect(popup_x, popup_y + 15, 30, 15)

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
            
        self.pickingStarted.emit()
        self.updateValue(event.pos())

    def mouseMoveEvent(self, event):
        self.updateValue(event.pos())
        
    def mouseReleaseEvent(self, event):
        if event.button() == RightButton:
            return
        self.is_picking = False
        self.pickingEnded.emit()
        self.update()

    def updateValue(self, pos):
        x = max(0, min(self.width(), pos.x()))
        y = max(0, min(self.height(), pos.y()))
        self.s = x / self.width()
        self.v = 1.0 - (y / self.height())
        self.update()
        self.emitColor()
        
    def emitColor(self):
        hp = self.hue / 60.0
        
        if self.mode == "v-hsv":
            s_adj = math.pow(self.s, (self.v + 0.5) / 1.5) if self.s > 0 else 0.0
            c = self.v * s_adj
        else:
            c = self.v * self.s
            
        x_val = c * (1 - abs(hp % 2 - 1))
        m = self.v - c
        
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

    def mouseReleaseEvent(self, event):
        if event.button() == RightButton:
            return
        self.is_picking = False
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
        self.main_layout.setSpacing(0)
        
        self.sv_square = SVSquare()
        self.hue_selector = HueSelector()
        self.history = ColorHistory()
        
        if "history" in self.config:
            hist_colors = [QColor(h) for h in self.config["history"]]
            while len(hist_colors) < 60: hist_colors.append(QColor(240, 240, 240))
            self.history.colors = hist_colors[:60]
        
        self.picker_container = PickerContainer(self.sv_square, self.hue_selector, self.history)
        
        self.main_layout.addWidget(self.picker_container, 1)
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
        

    def checkKritaColor(self):
        if not Krita.instance().activeWindow(): return
        view = Krita.instance().activeWindow().activeView()
        if not view: return
        
        try:
            qcolor = view.foregroundColor().colorForCanvas(view.canvas())
            
            if qcolor != self.last_color:
                self.last_color = qcolor
                
                if not self.sv_square.is_picking and not self.hue_selector.is_picking:
                    h, s, v, a = qcolor.getHsvF()
                    if h < 0: h = 0
                    
                    hue = h * 360.0
                    self.hue_selector.hue = hue
                    self.hue_selector.update()
                    
                    self.sv_square.hue = hue
                    self.sv_square.v = v
                    if self.sv_square.mode == "v-hsv":
                        if v == 0:
                            self.sv_square.s = 0.0
                        else:
                            import math
                            self.sv_square.s = math.pow(s, 1.5 / (v + 0.5))
                    else:
                        self.sv_square.s = s
                        
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
