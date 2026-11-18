from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QPen
from core.theme import BG_PANEL, TEXT_SECONDARY, BORDER, ACCENT_CYAN

# custom list with cyan border highlighting
class ItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # draw list item
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = option.rect
        selected = bool(option.state & QStyle.StateFlag.State_Selected)

        # background
        if selected:
            painter.fillRect(rect, QColor(BG_PANEL).lighter(120))
        else:
            painter.fillRect(rect, QColor(BG_PANEL))

        # line at bottom
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

        # cyan border when selected
        if selected:
            painter.setPen(QPen(QColor(ACCENT_CYAN), 1.5))
            painter.drawRect(rect.adjusted(1, 1, -2, -2))

        # text
        text = index.data(Qt.ItemDataRole.DisplayRole)
        text_rect = rect.adjusted(15, 5, -10, -5)
        painter.setPen(QColor(TEXT_SECONDARY))
        font = painter.font()
        font.setPixelSize(28)
        painter.setFont(font)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

        painter.restore()

    def sizeHint(self, option, index):
        # item height
        return QSize(0, 65)


class StyledListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegate(ItemDelegate())
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 4px;
                outline: none;
            }}
            QListWidget::item {{
                border: none;
                padding: 0px;
            }}
            QListWidget::item:hover {{
                background-color: rgba(0, 217, 255, 0.08);
            }}
        """)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def add_item(self, text, data=None):
        # add to list
        item = QListWidgetItem(text)
        if data:
            item.setData(Qt.ItemDataRole.UserRole, data)
        self.addItem(item)
