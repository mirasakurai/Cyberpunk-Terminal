import random
import json
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QUrl, QSize
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaMetaData
from pathlib import Path

from .wave_visualizer import WaveVisualizer
from .audio_analyzer import AudioAnalyzer
from .scrolling_text import ScrollingTextWidget
from core.theme import BG_PANEL, TEXT_PRIMARY, TEXT_SECONDARY, BORDER, ACCENT_CYAN

ROOT = Path(__file__).parent.parent.parent
MUSIC_DIR = ROOT / "data" / "music" / "Fists"
ASSETS_DIR = ROOT / "assets"


def _load_config():
    # load config json
    config_path = ROOT / "data" / "config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"current_date_ru": "пн 05.08.2045"}


CONFIG = _load_config()


# network traffic graph
class NetworkGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.data = [0.0] * 100  # rolling window
        self.speed = 0  # current speed

    def add_point(self, val):
        self.data.pop(0)
        self.data.append(val)
        self.speed = int(val * 1000)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(BG_PANEL))

        w, h = self.width(), self.height()

        pen = QPen(QColor(BORDER))
        pen.setWidth(1)
        p.setPen(pen)
        p.drawLine(0, h // 2, w, h // 2)  #center line
        for i in range(0, w, w // 10):  #vertical lines
            p.drawLine(i, 0, i, h)
        if len(self.data) > 1:
            pen = QPen(QColor(ACCENT_CYAN))
            pen.setWidth(2)
            p.setPen(pen)
            for i in range(len(self.data) - 1):
                x1 = int(i * w / len(self.data))
                y1 = int(h * 0.5 - (self.data[i] * h * 0.4))
                x2 = int((i + 1) * w / len(self.data))
                y2 = int(h * 0.5 - (self.data[i + 1] * h * 0.4))
                p.drawLine(x1, y1, x2, y2)


# right side info panel
class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_time = datetime.now()

        # music player
        self.player = QMediaPlayer()
        self.audio_out = QAudioOutput()
        self.player.setAudioOutput(self.audio_out)

        # audio analyzer for visualizer
        self.analyzer = AudioAnalyzer()
        self.player.setAudioBufferOutput(self.analyzer.get_audio_buffer_output())

        # playlist
        self.playlist = []
        self.current_idx = -1
        self.paused = False
        self._load_playlist()

        # signals
        self.player.mediaStatusChanged.connect(self._on_status)
        self.player.metaDataChanged.connect(self._update_track_info)

        self._init_ui()
        self._start_timer()

    def _load_playlist(self):
        # find all music files
        if MUSIC_DIR.exists():
            for ext in ["*.mp3", "*.wav", "*.flac", "*.ogg", "*.m4a"]:
                self.playlist.extend(sorted(MUSIC_DIR.glob(ext)))
            self.playlist = sorted(set(self.playlist))

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 25, 15, 15)
        layout.setSpacing(20)

        #date
        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet(f"font-size: 30px; color: {TEXT_PRIMARY}; background: transparent; border: none;")
        self.date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.date_lbl)
        layout.addSpacing(10)
        self._update_date()

        #system info box
        sys_frame = QFrame()
        sys_frame.setStyleSheet(f"QFrame {{ background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 6px; padding: 10px; }}")
        sys_layout = QVBoxLayout(sys_frame)
        sys_layout.setSpacing(12)

        title = QLabel("SYSTEM INFO")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {TEXT_SECONDARY}; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sys_layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {BORDER};")
        sep.setMaximumHeight(1)
        sys_layout.addWidget(sep)

        self.ip_lbl = QLabel("IPv4: 192.168.1.100")
        self.ip_lbl.setStyleSheet(f"font-size: 14px; color: {TEXT_PRIMARY};")
        sys_layout.addWidget(self.ip_lbl)

        self.status_lbl = QLabel("STATUS: ONLINE")
        self.status_lbl.setStyleSheet(f"font-size: 14px; color: {ACCENT_CYAN}; font-weight: bold;")
        sys_layout.addWidget(self.status_lbl)

        self.ping_lbl = QLabel("PING: -- ms")
        self.ping_lbl.setStyleSheet(f"font-size: 14px; color: {TEXT_PRIMARY};")
        sys_layout.addWidget(self.ping_lbl)

        self.ram_lbl = QLabel("RAM: 2.8TB / 8.0TB")
        self.ram_lbl.setStyleSheet(f"font-size: 14px; color: {TEXT_PRIMARY};")
        sys_layout.addWidget(self.ram_lbl)

        layout.addWidget(sys_frame)

        #network traffic box
        net_frame = QFrame()
        net_frame.setStyleSheet(f"QFrame {{ background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 6px; padding: 10px; }}")
        net_layout = QVBoxLayout(net_frame)
        net_layout.setSpacing(10)

        net_title = QLabel("NETWORK TRAFFIC")
        net_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {TEXT_SECONDARY}; letter-spacing: 2px;")
        net_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        net_layout.addWidget(net_title)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background-color: {BORDER};")
        sep2.setMaximumHeight(1)
        net_layout.addWidget(sep2)

        self.speed_lbl = QLabel("TRAFFIC: 0 MB/s")
        self.speed_lbl.setStyleSheet(f"font-size: 16px; color: {ACCENT_CYAN}; font-weight: bold;")
        self.speed_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        net_layout.addWidget(self.speed_lbl)

        self.graph = NetworkGraph()
        net_layout.addWidget(self.graph)

        layout.addWidget(net_frame)
        player_box = QFrame()
        player_box.setStyleSheet("background-color: transparent; border: none;")
        player_layout = QVBoxLayout(player_box)
        player_layout.setContentsMargins(0, 0, 0, 0)
        player_layout.setSpacing(0)

        # visualizer
        self.visualizer = WaveVisualizer()
        self.visualizer.setFixedHeight(110)
        self.visualizer.setStyleSheet("background-color: transparent; border: none;")
        self.visualizer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        player_layout.addWidget(self.visualizer)

        self.analyzer.levels_updated.connect(self.visualizer.set_levels)

        player_layout.addSpacing(12)


        btns = QHBoxLayout()
        btns.setSpacing(30)
        btns.setContentsMargins(0, 0, 0, 0)
        btns.addStretch()
        self.prev_btn = QPushButton()
        self.prev_btn.setFixedSize(48, 48)
        self.prev_btn.setIcon(QIcon(str(ASSETS_DIR / "previous.png")))
        self.prev_btn.setIconSize(QSize(40, 40))
        self.prev_btn.setStyleSheet("background-color: transparent; border: none;")
        self.prev_btn.clicked.connect(self._prev)
        btns.addWidget(self.prev_btn)
        self.play_btn = QPushButton()
        self.play_btn.setFixedSize(48, 48)
        self.play_btn.setIcon(QIcon(str(ASSETS_DIR / "play.png")))
        self.play_btn.setIconSize(QSize(40, 40))
        self.play_btn.setStyleSheet("background-color: transparent; border: none;")
        self.play_btn.clicked.connect(self._toggle_play)
        btns.addWidget(self.play_btn)
        self.next_btn = QPushButton()
        self.next_btn.setFixedSize(48, 48)
        self.next_btn.setIcon(QIcon(str(ASSETS_DIR / "next.png")))
        self.next_btn.setIconSize(QSize(40, 40))
        self.next_btn.setStyleSheet("background-color: transparent; border: none;")
        self.next_btn.clicked.connect(self._next)
        btns.addWidget(self.next_btn)

        btns.addStretch()
        player_layout.addLayout(btns)

        player_layout.addSpacing(6)

        #song name
        self.song_lbl = ScrollingTextWidget()
        self.song_lbl.setFixedHeight(24)
        self.song_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        player_layout.addWidget(self.song_lbl)

        layout.addWidget(player_box)
        layout.addStretch()

    def _start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(500)

    def _update_date(self):
        # set date label
        self.date_lbl.setText(CONFIG.get("current_date_ru", "пн 05.08.2045"))

    def _tick(self):
        #update every 500ms
        self._update_date()
        self.ping_lbl.setText(f"PING: {random.randint(8, 25)} ms")
        traffic = random.random()
        self.graph.add_point(traffic)
        self.speed_lbl.setText(f"TRAFFIC: {self.graph.speed} MB/s")

    def _toggle_play(self):
        #play or pause
        if not self.playlist:
            return
        if self.current_idx == -1:
            self._load_track(0)
            self.player.play()
            self.play_btn.setIcon(QIcon(str(ASSETS_DIR / "stop.png")))
            self.visualizer.set_playing(True)
            self.paused = False
        elif self.paused:
            self.player.play()
            self.play_btn.setIcon(QIcon(str(ASSETS_DIR / "stop.png")))
            self.visualizer.set_playing(True)
            self.paused = False
        else:
            self.player.pause()
            self.play_btn.setIcon(QIcon(str(ASSETS_DIR / "play.png")))
            self.visualizer.set_playing(False)
            self.paused = True

    def _next(self):
        if not self.playlist or self.current_idx == -1:
            return
        if self.current_idx < len(self.playlist) - 1:
            self._load_track(self.current_idx + 1)
            if not self.paused:
                self.player.play()

    def _prev(self):
        if not self.playlist or self.current_idx == -1:
            return
        if self.current_idx > 0:
            self._load_track(self.current_idx - 1)
            if not self.paused:
                self.player.play()

    def _load_track(self, idx):
        if 0 <= idx < len(self.playlist):
            self.current_idx = idx
            path = self.playlist[idx]
            self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))

    def _on_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.current_idx < len(self.playlist) - 1:
                # play next
                self._load_track(self.current_idx + 1)
                self.player.play()
            else:
                # playlist done
                self.current_idx = -1
                self.paused = False
                self.play_btn.setIcon(QIcon(str(ASSETS_DIR / "play.png")))
                self.visualizer.set_playing(False)
                self.song_lbl.set_text("")

    def _update_track_info(self):
        if self.current_idx == -1:
            self.song_lbl.set_text("")
            return

        meta = self.player.metaData()
        title = ""
        artist = ""

        if meta:
            title = meta.stringValue(QMediaMetaData.Key.Title)
            artist = meta.stringValue(QMediaMetaData.Key.ContributingArtist)
            if not artist:
                artist = meta.stringValue(QMediaMetaData.Key.AlbumArtist)

        # format display
        if title and artist:
            txt = f"{artist} — {title}"
        elif title:
            txt = title
        elif artist:
            txt = artist
        else:
            txt = self.playlist[self.current_idx].stem

        self.song_lbl.set_text(txt)
