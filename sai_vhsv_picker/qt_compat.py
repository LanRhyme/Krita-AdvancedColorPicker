try:
    from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QRect
    from PyQt6.QtGui import QPainter, QImage, QColor, QPen, QBrush, QCursor, QConicalGradient, QLinearGradient
    from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QBoxLayout, QGridLayout, QDockWidget, QPushButton, QDialog, QRadioButton, QGroupBox, QFormLayout, QCheckBox, QComboBox
    
    # Enums PyQt6
    ImageFormat_RGB32 = QImage.Format.Format_RGB32
    Color_black = Qt.GlobalColor.black
    Color_white = Qt.GlobalColor.white
    Color_transparent = Qt.GlobalColor.transparent
    RenderHint_SmoothPixmapTransform = QPainter.RenderHint.SmoothPixmapTransform
    RenderHint_Antialiasing = QPainter.RenderHint.Antialiasing
    BrushStyle_SolidPattern = Qt.BrushStyle.SolidPattern
    RightButton = Qt.MouseButton.RightButton
    Direction_BottomToTop = QBoxLayout.Direction.BottomToTop
    Direction_LeftToRight = QBoxLayout.Direction.LeftToRight
    AlignCenter = Qt.AlignmentFlag.AlignCenter
    
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF, QRect
    from PyQt5.QtGui import QPainter, QImage, QColor, QPen, QBrush, QCursor, QConicalGradient, QLinearGradient
    from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QBoxLayout, QGridLayout, QDockWidget, QPushButton, QDialog, QRadioButton, QGroupBox, QFormLayout, QCheckBox, QComboBox
    
    # Enums PyQt5
    ImageFormat_RGB32 = QImage.Format_RGB32
    Color_black = Qt.black
    Color_white = Qt.white
    Color_transparent = Qt.transparent
    RenderHint_SmoothPixmapTransform = QPainter.SmoothPixmapTransform
    RenderHint_Antialiasing = QPainter.Antialiasing
    BrushStyle_SolidPattern = Qt.SolidPattern
    RightButton = Qt.RightButton
    Direction_BottomToTop = QBoxLayout.BottomToTop
    Direction_LeftToRight = QBoxLayout.LeftToRight
    AlignCenter = Qt.AlignCenter
