from PyQt6.QtWidgets import QTabBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen
from core.theme import BG_TAB, ACCENT_CYAN, TEXT_SECONDARY, BORDER, BG_DARK

# skewed parallelogram tabs
class SkewedTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.skew = 15  # slant amount
        self.setDrawBase(False)
        self.setExpanding(False)
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)

    def paintEvent(self, event):
        # draw all tabs
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(BG_DARK))
        for i in range(self.count()):
            self._draw_tab(p, i)

    def _draw_tab(self, p, idx):
        rect = self.tabRect(idx)
        current = idx == self.currentIndex()

        # make parallelogram shape
        path = QPainterPath()
        path.moveTo(rect.left() + self.skew, rect.top())
        path.lineTo(rect.right() + self.skew, rect.top())
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()

        #color active tab cyan
        if current:
            p.fillPath(path, QColor(ACCENT_CYAN))
            p.setPen(QPen(QColor(ACCENT_CYAN), 2))
            p.drawPath(path)
            txt_color = QColor(BG_DARK)
        else:
            p.fillPath(path, QColor(BG_TAB))
            p.setPen(QPen(QColor(BORDER), 1))
            p.drawPath(path)
            txt_color = QColor(TEXT_SECONDARY)

        p.setPen(txt_color)
        font = p.font()
        font.setBold(current)
        font.setPixelSize(25)
        p.setFont(font)
        text_rect = rect.adjusted(self.skew // 2, 0, self.skew // 2, 0)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.tabText(idx))

    def tabSizeHint(self, idx):
        #tab width
        size = super().tabSizeHint(idx)
        size.setWidth(max(350, size.width() + 120))
        size.setHeight(60)
        return size

    def mousePressEvent(self, event):
        #handle tab click
        for i in range(self.count()):
            if self.tabRect(i).contains(event.pos()):
                self.setCurrentIndex(i)
                return
        super().mousePressEvent(event)
