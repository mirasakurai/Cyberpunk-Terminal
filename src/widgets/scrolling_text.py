# scrolling text for song name

import time
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor
from core.theme import TEXT_PRIMARY


class ScrollingTextWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(18)
        self.setMaximumHeight(18)

        self.text = ""
        self.offset = 0.0
        self.start_time = 0
        self.scrolling = False
        self.txt_w = 0
        self.vis_w = 0

        self.SPEED = 30  # px/sec
        self.PAUSE = 1.5  # sec before scroll
        self.GAP = 40

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def set_text(self, txt):
        self.text = txt
        self.offset = 0
        self.start_time = time.time()
        self.scrolling = False
        self.update()

    def _tick(self):
        if not self.text:
            return

        if not self.scrolling and self.txt_w > self.vis_w:
            if time.time() - self.start_time > self.PAUSE:
                self.scrolling = True

        if self.scrolling and self.txt_w > self.vis_w:
            self.offset = (time.time() - self.start_time - self.PAUSE) * self.SPEED

        self.update()

    def paintEvent(self, event):
        if not self.text:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        font = p.font()
        font.setPointSize(14)
        p.setFont(font)

        fm = p.fontMetrics()
        self.txt_w = fm.horizontalAdvance(self.text)
        self.vis_w = w - 32

        p.setPen(QColor(TEXT_PRIMARY))

        if self.txt_w <= self.vis_w:
            # fits - center it
            p.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, self.text)
        else:
            # scroll
            p.setClipRect(16, 0, w - 32, h)

            gap = " " * max(1, self.GAP // 8)
            loop = self.text + gap + self.text
            loop_w = fm.horizontalAdvance(loop)

            x = 16 - (self.offset % loop_w)
            p.drawText(int(x), 0, int(loop_w * 2), h,
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, loop)
