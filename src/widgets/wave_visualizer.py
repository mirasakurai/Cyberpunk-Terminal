# wave visualizer - animated sine waves

import math
import time
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QLinearGradient, QColor, QBrush
from core.theme import ACCENT_CYAN


class WaveVisualizer(QWidget):
    NUM_POINTS = 200
    MAX_H = 0.35
    LAYERS = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)

        self.color = QColor(ACCENT_CYAN)
        self.energy = 0.0
        self.bass = 0.0
        self.flow = 0.0
        self.last_t = time.monotonic()
        self.playing = False

        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(16)  # ~60fps

    def set_levels(self, levels):
        if not levels:
            return

        energy = sum(levels) / len(levels)
        bass_n = max(1, len(levels) // 8)
        bass = sum(levels[:bass_n]) / bass_n

        # smoothing
        d = energy - self.energy
        self.energy += d * (0.08 if d > 0 else 0.03)

        d = bass - self.bass
        self.bass += d * (0.15 if d > 0 else 0.04)

    def set_playing(self, val):
        self.playing = val

    def _update(self):
        now = time.monotonic()
        dt = min(now - self.last_t, 0.05)
        self.last_t = now

        if self.playing:
            speed = 0.8 + 0.6 * self.energy
            self.flow += dt * speed
        else:
            self.energy *= 0.95
            self.bass *= 0.95

        self.update()

    def _gradient(self, w):
        g = QLinearGradient(0, 0, w, 0)
        edge = QColor(self.color)
        edge.setAlpha(0)
        g.setColorAt(0.0, edge)
        g.setColorAt(0.25, self.color.lighter(130))
        g.setColorAt(0.5, self.color.lighter(160))
        g.setColorAt(0.75, self.color.lighter(130))
        g.setColorAt(1.0, edge)
        return g

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cy = h / 2
        mh = h * self.MAX_H

        grad = self._gradient(w)

        for layer in range(self.LAYERS):
            self._draw_layer(p, layer, w, h, cy, mh, grad)

    def _wave_y(self, x, offset):
        env = math.sin(math.pi * x) ** 2
        amp = (0.15 * self.energy + 0.85 * (self.energy ** 0.7)) * (1.0 + 0.3 * self.bass)

        w1 = 0.60 * math.sin(2 * math.pi * 1.0 * x + 0.9 * (self.flow + offset))
        w2 = 0.30 * math.sin(2 * math.pi * 1.7 * x - 0.6 * (self.flow + offset) + 1.3)
        w3 = 0.10 * math.sin(2 * math.pi * 2.6 * x + 1.4 * (self.flow + offset) + 2.1)

        return amp * env * (w1 + w2 + w3)

    def _draw_layer(self, p, layer, w, h, cy, mh, grad):
        offset = layer * 0.25
        amp = 1.0 - layer * 0.15

        pts = []
        for i in range(self.NUM_POINTS):
            x = i / (self.NUM_POINTS - 1)
            y = cy + self._wave_y(x, offset) * mh * amp
            pts.append((x * w, y))

        # glow
        glow_int = min(1, max(0, self.energy + 0.4 * self.bass))
        layer_op = 1.0 if layer == 0 else 0.4 + 0.2 * layer / self.LAYERS

        glow_color = QColor(self.color) if layer == 0 else self.color.darker(110 + layer * 10)

        for gw, go in [(16, 0.04), (9, 0.08), (4, 0.15)]:
            op = go * layer_op * glow_int
            glow_color.setAlpha(int(op * 255))
            p.setOpacity(op)
            pen = QPen(glow_color)
            pen.setWidth(gw)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            for i in range(len(pts) - 1):
                p.drawLine(int(pts[i][0]), int(pts[i][1]), int(pts[i+1][0]), int(pts[i+1][1]))

        # main line
        p.setOpacity(layer_op)
        pen = QPen(QBrush(grad), 1.5 if layer == 0 else 1.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for i in range(len(pts) - 1):
            p.drawLine(int(pts[i][0]), int(pts[i][1]), int(pts[i+1][0]), int(pts[i+1][1]))
