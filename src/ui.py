# main ui - edex style terminal

import sys
import random
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QSplitter, QFrame, QTextBrowser, QStatusBar,
    QGraphicsOpacityEffect, QPushButton, QGridLayout, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QUrl
from PyQt6.QtGui import QFont, QTextBlockFormat, QTextCursor, QPixmap, QFontDatabase
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

from app import Engine
from widgets import SkewedTabBar, StyledListWidget, RightPanel
from widgets.console_widget import ConsoleWidget
from core.theme import BG_DARK, BG_PANEL, ACCENT_CYAN, TEXT_PRIMARY, TEXT_SECONDARY, BORDER

# project root
ROOT = Path(__file__).parent.parent


def setup_fonts(app):
    fpath = str(ROOT / "assets" / "fonts" / "Rodchenko Regular.otf")
    fid = QFontDatabase.addApplicationFont(fpath)
    if fid == -1:
        font = QFont("Arial", 20)
    else:
        fams = QFontDatabase.applicationFontFamilies(fid)
        font = QFont(fams[0] if fams else "Arial", 20)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)


def load_stylesheet(app):
    qss = ROOT / "assets" / "main.qss"
    if qss.exists():
        with open(qss, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())


class CyberpunkTerminal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = Engine()
        self.sid = f"{random.randint(1000,9999):04X}-{random.randint(0,255):02X}{random.randint(0,255):02X}"

        # colors for chat participants
        self.colors = { 
            'shtanga': ACCENT_CYAN,
            'sh0v': "#004D00",
            'rjjavii': "#310000",
            'in3y': "#003441",
            'pr4vyi': "#4B2900",
            'lev4y4': "#440044",
            'k0styashhhhka': "#473333",
            're_ey': "#8AC57E",
            'tiktik': "#0B2E11",
        }

        self._init_ui()
        self._load_data()

    def _init_ui(self):
        self.setWindowTitle("EDEX Terminal")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        self.setGeometry(screen.availableGeometry())
        self.setStyleSheet(f"background-color: {BG_DARK};")

        central = QWidget()
        self.setCentralWidget(central)

        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # header
        main_lay.addWidget(self._make_header())

        # content
        content_lay = QHBoxLayout()
        content_lay.setContentsMargins(0, 0, 0, 0)
        content_lay.setSpacing(0)

        # tabs
        self.tabs = QTabWidget()
        self.tabs.setTabBar(SkewedTabBar())
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {BG_DARK};
                border: 1px solid {BORDER};
                border-top: 2px solid {ACCENT_CYAN};
            }}
        """)
        self.tabs.currentChanged.connect(self._on_tab_change)

        self._make_messages_tab()
        self._make_files_tab()
        self._make_network_tab()

        from core.tabs import Tab
        if self.engine.state.is_tab_enabled(Tab.CONSOLE):
            self._make_hacker_console_tab()
            self._make_console_tab()

        content_lay.addWidget(self.tabs)

        # right panel
        self.right_panel = RightPanel()
        self.right_panel.setMaximumWidth(400)
        content_lay.addWidget(self.right_panel)

        content_w = QWidget()
        content_w.setLayout(content_lay)
        main_lay.addWidget(content_w)

        self._make_statusbar()

        # website overlay
        self._setup_web_overlay()

    def _make_header(self):
        h = QFrame()
        h.setFixedHeight(50)
        h.setStyleSheet(f"QFrame {{ background-color: {BG_PANEL}; border-bottom: 2px solid {ACCENT_CYAN}; }}")

        lay = QHBoxLayout(h)
        lay.setContentsMargins(20, 10, 20, 10)

        title = QLabel("MAIN SHELL")
        title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {ACCENT_CYAN}; letter-spacing: 4px;")
        lay.addWidget(title)

        return h

    def _make_panel(self, title):
        # helper for creating panels
        p = QFrame()
        p.setStyleSheet(f"QFrame {{ background-color: {BG_PANEL}; border: 1px solid {BORDER}; }}")

        lay = QVBoxLayout(p)
        lay.setContentsMargins(20, 15, 20, 15)
        lay.setSpacing(15)

        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 40px; font-weight: bold; color: {TEXT_SECONDARY}; letter-spacing: 3px;")
        lay.addWidget(lbl)
        lay.setStretchFactor(lbl, 0)

        return p

    def _make_messages_tab(self):
        tab = QWidget()
        lay = QHBoxLayout(tab)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        split = QSplitter(Qt.Orientation.Horizontal)

        # left - list
        left = self._make_panel("MESSAGES")
        self.msg_list = StyledListWidget()
        self.msg_list.itemClicked.connect(self._on_msg_click)
        left.layout().addWidget(self.msg_list)
        split.addWidget(left)

        # right - content
        right = self._make_panel("CONTENT")
        self.msg_content = QTextBrowser()
        self.msg_content.setReadOnly(True)
        self.msg_content.setMarkdown("Select a message")
        self.msg_content.setStyleSheet(f"QTextBrowser {{ font-size: 20px; color: {TEXT_PRIMARY}; }}")
        right.layout().addWidget(self.msg_content)
        split.addWidget(right)

        split.setSizes([600, 1200])
        lay.addWidget(split)

        # opacity for animation
        self.msg_opacity = QGraphicsOpacityEffect()
        tab.setGraphicsEffect(self.msg_opacity)
        self.msg_opacity.setOpacity(1.0)

        self.tabs.addTab(tab, "◆  MESSAGES")

    def _make_files_tab(self):
        tab = QWidget()
        lay = QHBoxLayout(tab)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        split = QSplitter(Qt.Orientation.Horizontal)

        # left - list
        left = self._make_panel("FILES")
        self.file_list = StyledListWidget()
        self.file_list.itemClicked.connect(self._on_file_click)
        left.layout().addWidget(self.file_list)
        split.addWidget(left)

        # center - content area
        center = QFrame()
        center.setStyleSheet(f"QFrame {{ background-color: {BG_PANEL}; border: 1px solid {BORDER}; }}")
        center_lay = QVBoxLayout(center)
        center_lay.setContentsMargins(20, 15, 20, 15)
        center_lay.setSpacing(15)

        self.file_title = QLabel("CONTENT")
        self.file_title.setStyleSheet(f"font-size: 40px; font-weight: bold; color: {TEXT_SECONDARY}; letter-spacing: 3px;")
        center_lay.addWidget(self.file_title)

        # metadata
        self.file_meta = QTextBrowser()
        self.file_meta.setReadOnly(True)
        self.file_meta.setMaximumHeight(120)
        self.file_meta.setMinimumHeight(120)
        self.file_meta.setStyleSheet(f"QTextBrowser {{ font-size: 16px; color: {TEXT_PRIMARY}; background: transparent; border: none; }}")
        self.file_meta.hide()
        center_lay.addWidget(self.file_meta)

        # text content
        self.file_content = QTextBrowser()
        self.file_content.setReadOnly(True)
        self.file_content.setMarkdown("Select a file")
        self.file_content.setStyleSheet(f"QTextBrowser {{ font-size: 20px; color: {TEXT_PRIMARY}; }}")
        center_lay.addWidget(self.file_content)

        # video player
        self.vid_player = QMediaPlayer()
        self.vid_widget = QVideoWidget()
        self.vid_player.setVideoOutput(self.vid_widget)
        self.vid_audio = QAudioOutput()
        self.vid_player.setAudioOutput(self.vid_audio)
        self.vid_widget.setStyleSheet(f"QVideoWidget {{ background-color: #1a1a1a; border: 2px solid {ACCENT_CYAN}; }}")
        self.vid_widget.setMinimumSize(640, 360)
        self.vid_widget.hide()

        self.vid_player.errorOccurred.connect(lambda e, s: None)
        self.vid_player.mediaStatusChanged.connect(self._on_vid_status)
        self.vid_player.playbackStateChanged.connect(self._on_vid_state)
        self._show_first_frame = False

        center_lay.addWidget(self.vid_widget)

        # video controls
        vid_ctrl = QWidget()
        vid_ctrl_lay = QHBoxLayout(vid_ctrl)
        vid_ctrl_lay.setContentsMargins(0, 5, 0, 0)

        self.vid_btn = QPushButton("▶")
        self.vid_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ACCENT_CYAN}; color: {BG_DARK}; font-size: 24px; font-weight: bold; padding: 10px 20px; border: none; }}
            QPushButton:hover {{ background-color: #00d4ff; }}
        """)
        self.vid_btn.clicked.connect(self._toggle_vid)
        vid_ctrl_lay.addWidget(self.vid_btn)
        vid_ctrl_lay.addStretch()

        self.vid_ctrl = vid_ctrl
        self.vid_ctrl.hide()
        center_lay.addWidget(self.vid_ctrl)

        # audio player
        self.aud_player = QMediaPlayer()
        self.aud_out = QAudioOutput()
        self.aud_player.setAudioOutput(self.aud_out)

        self.aud_player.playbackStateChanged.connect(self._on_aud_state)
        self.aud_player.mediaStatusChanged.connect(self._on_aud_status)
        self.aud_player.errorOccurred.connect(lambda e, s: None)

        # audio widget
        self.aud_widget = QWidget()
        aud_lay = QVBoxLayout(self.aud_widget)
        aud_lay.setContentsMargins(0, 20, 0, 20)
        aud_lay.setSpacing(15)

        aud_container = QWidget()
        aud_c_lay = QHBoxLayout(aud_container)
        aud_c_lay.addStretch()

        self.aud_btn = QPushButton("▶")
        self.aud_btn.setFixedSize(80, 80)
        self.aud_btn.setStyleSheet(f"""
            QPushButton {{ background-color: #404040; color: #fff; border-radius: 40px; border: none; font-size: 32px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #535353; }}
            QPushButton:pressed {{ background-color: #2a2a2a; }}
        """)
        self.aud_btn.clicked.connect(self._toggle_aud)
        aud_c_lay.addWidget(self.aud_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        aud_c_lay.addStretch()
        aud_lay.addWidget(aud_container)

        self.aud_name = QLabel("Select a track")
        self.aud_name.setStyleSheet(f"QLabel {{ color: {TEXT_PRIMARY}; font-size: 16px; font-weight: bold; }}")
        self.aud_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        aud_lay.addWidget(self.aud_name)
        aud_lay.addStretch()

        self.aud_widget.hide()
        center_lay.addWidget(self.aud_widget)

        # stretch factors
        center_lay.setStretchFactor(self.file_title, 0)
        center_lay.setStretchFactor(self.file_meta, 0)
        center_lay.setStretchFactor(self.file_content, 1)
        center_lay.setStretchFactor(self.vid_widget, 1)
        center_lay.setStretchFactor(self.aud_widget, 1)

        split.addWidget(center)
        split.setSizes([400, 800, 400])
        lay.addWidget(split)

        self.file_opacity = QGraphicsOpacityEffect()
        tab.setGraphicsEffect(self.file_opacity)
        self.file_opacity.setOpacity(1.0)

        self.tabs.addTab(tab, "▢  FILES")

    def _make_network_tab(self):
        tab = QWidget()
        main_lay = QVBoxLayout(tab)
        main_lay.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("NETWORK MAP")
        lbl.setStyleSheet(f"font-size: 40px; font-weight: bold; color: {TEXT_SECONDARY};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_lay.addWidget(lbl)

        # grid of site icons
        grid_w = QWidget()
        self.net_grid = QGridLayout(grid_w)
        self.net_grid.setSpacing(100)
        self.net_grid.setContentsMargins(30, 30, 30, 30)

        icons_dir = ROOT / "data" / "sites" / "icons"
        self.site_icons = []
        if icons_dir.exists():
            for f in sorted(icons_dir.glob("*.*")):
                if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                    self.site_icons.append(f)

        icon_sz = 300
        cols = 3

        for i, icon_path in enumerate(self.site_icons):
            name = icon_path.stem.replace("_square", "").replace("_icon", "")
            html_path = ROOT / "data" / "sites" / f"{name}.html"

            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedSize(icon_sz, icon_sz)
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            lbl.setStyleSheet(f"QLabel {{ background-color: {BG_PANEL}; border: 2px solid {BORDER}; }} QLabel:hover {{ border: 2px solid {ACCENT_CYAN}; }}")
            lbl.setProperty("html_path", str(html_path))
            lbl.mousePressEvent = lambda e, p=html_path: self._open_site(p)

            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                scaled = pix.scaled(icon_sz - 4, icon_sz - 4, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                lbl.setPixmap(scaled)

            self.net_grid.addWidget(lbl, i // cols, i % cols)

        h_lay = QHBoxLayout()
        h_lay.addStretch()
        h_lay.addWidget(grid_w)
        h_lay.addStretch()
        main_lay.addLayout(h_lay)
        main_lay.addStretch()

        self.net_opacity = QGraphicsOpacityEffect()
        tab.setGraphicsEffect(self.net_opacity)
        self.net_opacity.setOpacity(1.0)

        self.tabs.addTab(tab, "◈  NETWORK")

    def _make_hacker_console_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.hacker_console = ConsoleWidget(self)
        lay.addWidget(self.hacker_console)

        self.console_opacity = QGraphicsOpacityEffect()
        tab.setGraphicsEffect(self.console_opacity)
        self.console_opacity.setOpacity(1.0)

        self.tabs.addTab(tab, "▶  TERMINAL")

    def _make_console_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("CONSOLE ACCESS")
        lbl.setStyleSheet(f"font-size: 40px; font-weight: bold; color: {TEXT_SECONDARY};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)

        self.console_opacity = QGraphicsOpacityEffect()
        tab.setGraphicsEffect(self.console_opacity)
        self.console_opacity.setOpacity(1.0)

        self.tabs.addTab(tab, "▶▶  CONSOLE")

    def _make_statusbar(self):
        sb = QStatusBar()
        sb.setStyleSheet(f"QStatusBar {{ background-color: {BG_PANEL}; color: {TEXT_SECONDARY}; border-top: 1px solid {BORDER}; font-size: 45px; }}")

        sb.addWidget(QLabel("v1.0.0"))
        sb.addWidget(QLabel(f"SESSION: {self.sid}"))
        sb.addPermanentWidget(QLabel(f"ID: {self.sid[:4]}"))

        self.setStatusBar(sb)

    def _setup_web_overlay(self):
        # overlay for opening sites
        self.web_overlay = QFrame(self)
        self.web_overlay.setStyleSheet(f"QFrame {{ background-color: {BG_DARK}; }}")
        self.web_overlay.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.web_opacity = QGraphicsOpacityEffect()
        self.web_overlay.setGraphicsEffect(self.web_opacity)
        self.web_opacity.setOpacity(0.0)
        self.web_overlay.hide()

        self.web_view = QWebEngineView(self.web_overlay)

        from PyQt6.QtWebEngineCore import QWebEngineProfile
        prof = self.web_view.page().profile()
        prof.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)

        self.web_view.setStyleSheet(f"QWebEngineView {{ background-color: {BG_DARK}; border: none; margin: 0; padding: 0; }}")

        self.web_loading = QLabel("Loading...", self.web_overlay)
        self.web_loading.setStyleSheet(f"QLabel {{ background-color: {BG_DARK}; color: {ACCENT_CYAN}; font-size: 18px; border: none; }}")
        self.web_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.web_loading.hide()

        self.web_view.loadStarted.connect(self._on_web_start)
        self.web_view.loadFinished.connect(self._on_web_finish)

        self.web_close_btn = QPushButton("✕")
        self.web_close_btn.setParent(self.web_overlay)
        self.web_close_btn.setFixedSize(40, 40)
        self.web_close_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ACCENT_CYAN}; color: {BG_DARK}; border: none; border-radius: 20px; font-size: 24px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #00d4ff; }}
        """)
        self.web_close_btn.clicked.connect(self._close_site)
        self.web_close_btn.raise_()

    # --- data loading ---

    def _load_data(self):
        msgs = self.engine.get_messages()
        for mid, msg in msgs.items():
            subj = msg.get('subject', 'No Subject') if isinstance(msg, dict) else 'Message'
            self.msg_list.add_item(subj, msg)

        files = self.engine.get_files()
        for fid, fdata in files.items():
            if isinstance(fdata, dict):
                name = fdata.get('name', 'Unnamed')
                self.file_list.add_item(name, fdata)

    # --- handlers ---

    def _on_msg_click(self, item):
        msg = item.data(Qt.ItemDataRole.UserRole)
        if not msg or 'thread' not in msg:
            return

        html = f"""
        <style>
            body {{ font-family: Arial; color: {TEXT_PRIMARY}; font-size: 30px; }}
            .header {{ margin-bottom: 20px; }}
            .subject {{ font-size: 32px; font-weight: bold; color: {ACCENT_CYAN}; }}
            .meta {{ font-size: 18px; color: {TEXT_SECONDARY}; margin: 5px 0; }}
            .message {{ margin: 0 40px 0 10px; padding: 0; border-left: 3px solid {ACCENT_CYAN}; font-size: 22px; }}
            .sender {{ font-weight: bold; color: {ACCENT_CYAN}; font-size: 26px; margin-bottom: 2px; }}
            .timestamp {{ font-size: 12px; color: {TEXT_SECONDARY}; margin: 0 0 4px 0; display: block; }}
            .text {{ margin: 0 0 30px 0; white-space: pre-wrap; font-size: 28px; }}
            .image {{ max-width: 80%; max-height: 340px; margin: 0; display: block; }}
            hr {{ border: none; border-top: 1px solid {BORDER}; margin: 20px 0; }}
        </style>
        <div class="header">
            <div class="subject">{msg.get('subject', 'N/A')}</div>
            <div class="meta">Participants: {', '.join(msg.get('participants', []))}</div>
            <div class="meta">Date: {msg.get('date', 'N/A')}</div>
        </div>
        <hr>
        """

        for m in msg['thread']:
            sender = m.get("sender", "Unknown")
            color = self.colors.get(sender, ACCENT_CYAN)
            html += f'<div class="message"><div class="sender" style="color: {color};">{sender}</div>'
            html += f'<div class="timestamp">{m.get("timestamp", "N/A")}</div>'
            html += f'<div class="text">{m.get("text", "")}</div>'

            if m.get('image'):
                img = m['image']
                if not img.startswith('file://'):
                    # convert to file:// url
                    img = 'file:///' + Path(img).resolve().as_posix()
                html += f'<img src="{img}" class="image">'

            html += '</div>'

        self.msg_content.setHtml(html)
        self._set_spacing(self.msg_content, 100)

    def _on_file_click(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        # audio file?
        if data.get('audio'):
            path = str(Path(data['audio']).resolve())
            self._show_file_meta(data)
            self.file_content.hide()
            self.vid_widget.hide()
            self.vid_ctrl.hide()
            self.aud_widget.show()
            self.aud_btn.setText("▶")
            self.aud_name.setText(data.get('name', 'Unknown'))
            self.aud_player.setSource(QUrl.fromLocalFile(path))
            return

        # video file?
        if data.get('video'):
            path = str(Path(data['video']).resolve())
            self._show_file_meta(data)
            self.file_content.hide()
            self.vid_widget.show()
            self.vid_ctrl.show()
            self.aud_widget.hide()
            self.vid_btn.setText("▶")
            self._show_first_frame = True
            self.vid_player.setSource(QUrl.fromLocalFile(path))
            return

        # regular file
        self.vid_widget.hide()
        self.vid_ctrl.hide()
        self.aud_widget.hide()
        self.file_meta.hide()
        self.file_content.show()
        self.vid_player.stop()
        self.aud_player.stop()

        html = f"""
        <style>
            body {{ font-family: Arial; color: {TEXT_PRIMARY}; font-size: 30px; line-height: 1; margin: 0; padding: 0; }}
            img {{ display: block; vertical-align: top; }}
            .header {{ margin-bottom: 20px; }}
            .filename {{ font-size: 32px; font-weight: bold; color: {ACCENT_CYAN}; }}
            .meta {{ font-size: 18px; color: {TEXT_SECONDARY}; margin: 5px 0; }}
            .content {{ margin: 20px 0 15px 0; white-space: pre-wrap; font-size: 24px; }}
            .image {{ max-width: 90%; max-height: 380px; margin: 3px 0; }}
            hr {{ border: none; border-top: 1px solid {BORDER}; margin: 20px 0; }}
        </style>
        <div class="header">
            <div class="filename">{data.get('name', 'Unknown')}</div>
            <div class="meta">Type: {data.get('type', 'N/A')}</div>
            <div class="meta">Size: {data.get('size', 'N/A')}</div>
            <div class="meta">Date: {data.get('date', 'N/A')}</div>
        </div>
        <hr>
        """

        if data.get('image'):
            img = data['image']
            if not img.startswith('file://'):
                # convert to file:// url
                img = 'file:///' + Path(img).resolve().as_posix()
            html += f'<img src="{img}" class="image">'
        else:
            html += f'<div class="content">{data.get("content", "No content")}</div>'

        html += "</div>"
        self.file_content.setHtml(html)
        self._set_spacing(self.file_content, 120)

    def _show_file_meta(self, data):
        html = f"""
        <style>
            body {{ font-family: Arial; color: {TEXT_PRIMARY}; font-size: 20px; margin: 0; padding: 0; }}
            .filename {{ font-size: 28px; font-weight: bold; color: {ACCENT_CYAN}; margin-bottom: 10px; }}
            .meta {{ font-size: 18px; color: {TEXT_SECONDARY}; margin: 3px 0; }}
        </style>
        <div class="filename">{data.get('name', 'Unknown')}</div>
        <div class="meta">Type: {data.get('type', 'N/A')}</div>
        <div class="meta">Size: {data.get('size', 'N/A')}</div>
        <div class="meta">Date: {data.get('date', 'N/A')}</div>
        """
        self.file_meta.setHtml(html)
        self.file_meta.show()

    def _set_spacing(self, browser, pct=150):
        cur = QTextCursor(browser.document())
        cur.select(QTextCursor.SelectionType.Document)
        fmt = QTextBlockFormat()
        fmt.setLineHeight(pct, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        cur.mergeBlockFormat(fmt)

    # --- video ---

    def _on_vid_status(self, status):
        if self._show_first_frame and status == QMediaPlayer.MediaStatus.LoadedMedia:
            self._show_first_frame = False
            self.vid_player.play()
            QTimer.singleShot(100, lambda: (self.vid_player.pause(), self.vid_player.setPosition(0)))
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.vid_player.setPosition(0)
            self.vid_btn.setText("▶")

    def _on_vid_state(self, state):
        self.vid_btn.setText("||" if state == QMediaPlayer.PlaybackState.PlayingState else "▶")

    def _toggle_vid(self):
        if self.vid_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.vid_player.pause()
        else:
            self.vid_player.play()

    # --- audio ---

    def _on_aud_state(self, state):
        self.aud_btn.setText("||" if state == QMediaPlayer.PlaybackState.PlayingState else "▶")

    def _on_aud_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.aud_player.pause()
            self.aud_player.setPosition(0)
            self.aud_btn.setText("▶")

    def _toggle_aud(self):
        if self.aud_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.aud_player.pause()
        else:
            self.aud_player.play()

    # --- tab animation ---

    def _on_tab_change(self, idx):
        w = self.tabs.widget(idx)
        if not w:
            return
        eff = w.graphicsEffect()
        if isinstance(eff, QGraphicsOpacityEffect):
            self.tab_anim = QPropertyAnimation(eff, b"opacity")
            self.tab_anim.setDuration(300)
            self.tab_anim.setStartValue(0.0)
            self.tab_anim.setEndValue(1.0)
            self.tab_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.tab_anim.start()

    # --- website overlay ---

    def _on_web_start(self):
        self.web_loading.show()
        self.web_view.hide()
        if hasattr(self, 'load_timer'):
            self.load_timer.stop()
        self.load_timer = QTimer()
        self.load_timer.setSingleShot(True)
        self.load_timer.timeout.connect(lambda: (self.web_view.stop(), self._on_web_finish(False)))
        self.load_timer.start(8000)

    def _on_web_finish(self, ok):
        if hasattr(self, 'load_timer'):
            self.load_timer.stop()
        self.web_loading.hide()
        self.web_view.show()

        # kill heavy animations
        css = "* { animation-duration: 0s !important; transition-duration: 0s !important; } body { scroll-behavior: auto !important; } * { backdrop-filter: none !important; }"
        js = f"(function(){{ const s = document.createElement('style'); s.textContent = `{css}`; document.head.appendChild(s); }})();"
        self.web_view.page().runJavaScript(js)

    def _open_site(self, path):
        if not path.exists():
            return
        self.web_view.setUrl(QUrl.fromLocalFile(str(path.resolve())))
        self.web_overlay.setGeometry(self.rect())
        self.web_view.setGeometry(0, 0, self.width(), self.height())
        self.web_loading.setGeometry(0, 0, self.width(), self.height())
        self.web_close_btn.move(self.width() - 50, 10)
        self.web_overlay.show()
        self.web_overlay.raise_()
        self.web_close_btn.raise_()

        self.web_fade_in = QPropertyAnimation(self.web_opacity, b"opacity")
        self.web_fade_in.setDuration(400)
        self.web_fade_in.setStartValue(0.0)
        self.web_fade_in.setEndValue(1.0)
        self.web_fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.web_fade_in.start()

    def _close_site(self):
        self.web_fade_out = QPropertyAnimation(self.web_opacity, b"opacity")
        self.web_fade_out.setDuration(300)
        self.web_fade_out.setStartValue(1.0)
        self.web_fade_out.setEndValue(0.0)
        self.web_fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.web_fade_out.finished.connect(lambda: (self.web_overlay.hide(), self.web_view.setUrl(QUrl("about:blank"))))
        self.web_fade_out.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'web_overlay') and self.web_overlay.isVisible():
            self.web_overlay.setGeometry(self.rect())
            self.web_view.setGeometry(0, 0, self.width(), self.height())
            self.web_loading.setGeometry(0, 0, self.width(), self.height())
            self.web_close_btn.move(self.width() - 50, 10)


def main():
    try:
        import warnings
        warnings.filterwarnings("ignore")

        # suppress ffmpeg logs on windows
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.kernel32.SetStdHandle(-12, None)

        app = QApplication(sys.argv)
        setup_fonts(app)
        load_stylesheet(app)

        win = CyberpunkTerminal()
        win.show()

        sys.exit(app.exec())
    except Exception as e:
        print(f"error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
