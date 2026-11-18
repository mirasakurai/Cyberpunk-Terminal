import random
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QKeyEvent

from core.console_system import ConsoleSystem
from core.theme import BG_DARK, ACCENT_CYAN, BORDER

ROOT = Path(__file__).parent.parent.parent

MATRIX_GREEN = "#00ff6a"
MATRIX_DARK_GREEN = "#00aa44"


class ConsoleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.console_system = ConsoleSystem()
        self.state = "locked"  # locked, typing, wait_confirm, terminal, denied
        self.input_password = ""
        self.password_success = False

        # Текущий ввод в терминале
        self.current_input = ""
        self.history_index = -1

        self._init_ui()
        self._setup_styles()

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._blink_cursor)
        self.blink_timer.start(500)
        self.blink_state = True

        # Для захвата клавиатуры
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.screen = ScreenWidget(self)
        main_layout.addWidget(self.screen, 1)

        self.setLayout(main_layout)
        self._show_locked_screen()
        self._create_test_buttons()

    def _create_test_buttons(self):
        """Временные тестовые кнопки для симуляции Telegram-команд"""
        self.test_success_btn = QPushButton("TEST /success", self)
        self.test_success_btn.setFont(QFont("Courier New", 10))
        self.test_success_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #004400;
                color: {MATRIX_GREEN};
                border: 1px solid {MATRIX_GREEN};
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: #006600;
            }}
        """)
        self.test_success_btn.clicked.connect(lambda: self.process_telegram_command("/success"))
        self.test_success_btn.move(10, 10)
        self.test_success_btn.show()

        self.test_false_btn = QPushButton("TEST /false", self)
        self.test_false_btn.setFont(QFont("Courier New", 10))
        self.test_false_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #440000;
                color: #ff4444;
                border: 1px solid #ff4444;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: #660000;
            }}
        """)
        self.test_false_btn.clicked.connect(lambda: self.process_telegram_command("/false"))
        self.test_false_btn.move(130, 10)
        self.test_false_btn.show()

    def _setup_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
        """)

    def _blink_cursor(self):
        self.blink_state = not self.blink_state
        self.screen.update()

    def _show_locked_screen(self):
        self.state = "locked"
        self.input_password = ""
        self.screen.input_text = ""
        self.screen.update()

    def process_telegram_command(self, command: str):
        if self.state == "denied":
            return

        if self.state != "locked":
            return

        if command == "/success":
            self._animate_success()
        elif command == "/false":
            self._animate_failure()

    def _animate_success(self):
        self.state = "typing"
        self.password_success = True
        correct_pwd = self.console_system.config.get("correct_password", "1234")
        self._animate_password(correct_pwd)

    def _animate_failure(self):
        self.state = "typing"
        self.password_success = False
        wrong_pwd = self._generate_wrong_password()
        self._animate_password(wrong_pwd)

    def _generate_wrong_password(self) -> str:
        chars = "0123456789"
        return "".join(random.choice(chars) for _ in range(6))

    def _animate_password(self, target_password: str):
        self.input_password = ""
        self.screen.input_text = ""

        def type_char(index):
            if index < len(target_password):
                self.input_password += target_password[index]
                self.screen.input_text = self.input_password
                self.screen.update()
                QTimer.singleShot(150, lambda: type_char(index + 1))
            else:
                # Анимация закончена — ждём нажатия кнопки
                self.state = "wait_confirm"
                self.screen.update()

        type_char(0)

    def on_submit_clicked(self):
        if self.state == "wait_confirm":
            if self.password_success:
                self._on_password_success()
            else:
                self._on_password_failure()

    def _on_password_success(self):
        self.state = "terminal"
        self.screen.terminal_history = []
        self.current_input = ""
        self.setFocus()  # Захватываем фокус для ввода
        self.screen.update()

    def _on_password_failure(self):
        self.state = "denied"
        self.screen.update()

    def keyPressEvent(self, event: QKeyEvent):
        if self.state != "terminal":
            return

        key = event.key()

        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            self._execute_command()
        elif key == Qt.Key.Key_Backspace:
            self.current_input = self.current_input[:-1]
            self.screen.update()
        elif key == Qt.Key.Key_Up:
            self._history_up()
        elif key == Qt.Key.Key_Down:
            self._history_down()
        else:
            text = event.text()
            if text and text.isprintable():
                self.current_input += text
                self.screen.update()

    def _execute_command(self):
        cmd = self.current_input
        self.current_input = ""
        self.history_index = -1
        prompt = self.console_system.get_prompt()

        if cmd.strip():
            output = self.console_system.execute_command(cmd)

            if output == "__CLEAR__":
                self.screen.terminal_history = []
                self.screen.scroll_offset = 0
            else:
                self.screen.add_command(prompt, cmd, output)
        else:
            self.screen.add_command(prompt, "", "")

        self.screen.update()

    def _history_up(self):
        history = self.console_system.command_history
        if not history:
            return

        if self.history_index < len(history) - 1:
            self.history_index += 1
            self.current_input = history[-(self.history_index + 1)]
            self.screen.update()

    def _history_down(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_input = self.console_system.command_history[-(self.history_index + 1)]
            self.screen.update()
        elif self.history_index == 0:
            self.history_index = -1
            self.current_input = ""
            self.screen.update()

    def mousePressEvent(self, event):
        if self.state == "terminal":
            self.setFocus()
        super().mousePressEvent(event)


class ScreenWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_console = parent
        self.input_text = ""
        self.terminal_history = []  # [(prompt, cmd, output), ...]
        self.scroll_offset = 0

        self.submit_btn = QPushButton(">", self)
        self.submit_btn.setFont(QFont("Courier New", 20, QFont.Weight.Bold))
        self.submit_btn.setFixedSize(50, 40)
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MATRIX_GREEN};
                color: #000000;
                border: none;
                font-size: 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #00ff99;
            }}
            QPushButton:pressed {{
                background-color: #00cc55;
            }}
        """)
        self.submit_btn.clicked.connect(self._on_submit)
        self.submit_btn.hide()

        self.code_lines = []
        self.asm_opcodes = ["MOV", "JMP", "NOP", "XOR", "AND", "OR", "SUB", "ADD", "PUSH", "POP", "CALL", "RET", "CMP", "JNE", "JEQ", "LEA", "INC", "DEC", "SHL", "SHR", "TEST", "INT"]
        self.hex_regs = ["EAX", "EBX", "ECX", "EDX", "ESP", "EBP", "ESI", "EDI", "RAX", "RBX", "RCX", "RDX", "R8", "R9", "R10", "R11"]

        self.matrix_timer = QTimer()
        self.matrix_timer.timeout.connect(self._update_matrix)
        self.matrix_timer.start(100)

        self._init_code_lines()

    def _on_submit(self):
        self.parent_console.on_submit_clicked()

    def _init_code_lines(self):
        self.code_lines = []
        num_lines = 40
        for i in range(num_lines):
            line = {
                'y': random.randint(-800, self.height() if self.height() > 0 else 600),
                'speed': random.uniform(0.3, 1.2),
                'text': self._generate_code_line(),
                'opacity': random.uniform(0.06, 0.18)
            }
            self.code_lines.append(line)

    def _generate_code_line(self) -> str:
        line_type = random.choice(['asm', 'asm', 'hex', 'hex', 'binary', 'multi_asm', 'dump', 'comment'])
        if line_type == 'asm':
            op = random.choice(self.asm_opcodes)
            reg1 = random.choice(self.hex_regs)
            if random.random() > 0.5:
                reg2 = random.choice(self.hex_regs)
                offset = hex(random.randint(0, 0xFFFF))
                return f"{op} {reg1}, {reg2}    ; offset {offset}"
            else:
                val = hex(random.randint(0, 0xFFFFFF))
                return f"{op} {reg1}, {val}           ; immediate"
        elif line_type == 'hex':
            addr = ''.join(random.choices('0123456789ABCDEF', k=8))
            data = ' '.join(''.join(random.choices('0123456789ABCDEF', k=2)) for _ in range(random.randint(8, 16)))
            return f"0x{addr}: {data}"
        elif line_type == 'binary':
            return ''.join(random.choices('01', k=random.randint(32, 64)))
        elif line_type == 'multi_asm':
            ops = random.sample(self.asm_opcodes, 3)
            regs = random.sample(self.hex_regs, 4)
            return f"{ops[0]} {regs[0]}, {regs[1]} | {ops[1]} {regs[2]} | {ops[2]} {regs[3]}, 0x{random.randint(0,255):02X}"
        elif line_type == 'dump':
            addr = ''.join(random.choices('0123456789ABCDEF', k=8))
            ascii_chars = ''.join(random.choices('._@#$%ABCDEFabcdef0123', k=16))
            hex_part = ' '.join(''.join(random.choices('0123456789ABCDEF', k=2)) for _ in range(8))
            return f"{addr}  {hex_part}  |{ascii_chars}|"
        elif line_type == 'comment':
            comments = [
                "; === INIT STACK FRAME === decrypt payload buffer",
                "; CHECK ACCESS LEVEL >> verify signature hash",
                "; LOAD MODULE 0x7FFE >> inject shellcode routine",
                "; BYPASS SECURITY CHECK >> escalate privileges",
                "; MEMORY SCAN COMPLETE >> found 3 targets",
                "; DECRYPTING STREAM >> AES-256-CBC mode active"
            ]
            return random.choice(comments)
        else:
            addr = ''.join(random.choices('0123456789ABCDEF', k=8))
            return f"syscall 0x{random.randint(0, 255):02X} @ 0x{addr} >> RET={random.randint(0,1)}"

    def _update_matrix(self):
        for line in self.code_lines:
            line['y'] += line['speed']
            if line['y'] > self.height() + 50:
                line['y'] = random.randint(-100, -20)
                line['text'] = self._generate_code_line()
                line['speed'] = random.uniform(0.3, 1.2)
                line['opacity'] = random.uniform(0.06, 0.18)
        self.update()

    def add_command(self, prompt: str, cmd: str, output: str):
        self.terminal_history.append((prompt, cmd, output))
        self.scroll_offset = 0

    def wheelEvent(self, event):
        if self.parent_console.state != "terminal":
            return

        delta = event.angleDelta().y()
        if delta > 0:
            self.scroll_offset += 3
        else:
            self.scroll_offset -= 3
            if self.scroll_offset < 0:
                self.scroll_offset = 0

        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_submit_btn()

    def _position_submit_btn(self):
        box_width = 500
        box_x = (self.width() - box_width) // 2 - 100
        box_y = (self.height() - 280) // 2
        input_y = box_y + 140

        btn_x = box_x + box_width - 20 - 50
        btn_y = input_y
        self.submit_btn.move(btn_x, btn_y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        state = self.parent_console.state

        if state == "denied":
            painter.fillRect(self.rect(), QColor(40, 5, 5))
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0))

        #matrix-код справа
        self._draw_matrix_rain(painter)

        if state in ["locked", "typing", "wait_confirm"]:
            self._draw_locked_screen(painter)
            self._position_submit_btn()
            if state == "wait_confirm":
                self.submit_btn.show()
            else:
                self.submit_btn.hide()
        elif state == "terminal":
            self.submit_btn.hide()
            self._draw_terminal(painter)
        elif state == "denied":
            self.submit_btn.hide()
            self._draw_denied_screen(painter)

    def _draw_matrix_rain(self, painter):
        font = QFont("Courier New", 9)
        painter.setFont(font)

        start_x = int(self.width() * 0.68)

        for line in self.code_lines:
            painter.setOpacity(line['opacity'])

            green_val = random.randint(150, 255)
            painter.setPen(QColor(0, green_val, int(green_val * 0.3)))

            y = int(line['y'])
            painter.drawText(start_x, y, line['text'])

        painter.setOpacity(1.0)

    def _draw_locked_screen(self, painter):
        box_width = 500
        box_height = 280
        box_x = (self.width() - box_width) // 2 - 100
        box_y = (self.height() - box_height) // 2

        painter.fillRect(box_x, box_y, box_width, box_height, QColor(5, 5, 5))

        pen = QPen(QColor(MATRIX_GREEN), 2)
        painter.setPen(pen)
        painter.drawRect(box_x, box_y, box_width, box_height)

        header_height = 50
        painter.fillRect(box_x, box_y, box_width, header_height, QColor(180, 20, 30))
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Courier New", 18)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(box_x, box_y, box_width, header_height,
                        Qt.AlignmentFlag.AlignCenter, "PASSWORD REQUIRED")

        painter.setPen(QColor(MATRIX_GREEN))
        font = QFont("Courier New", 12)
        painter.setFont(font)
        painter.drawText(box_x + 20, box_y + 70, box_width - 40, 40,
                        Qt.TextFlag.TextWordWrap, "Enter password to access system")

        input_y = box_y + 140
        input_width = box_width - 40 - 60
        painter.fillRect(box_x + 20, input_y, input_width, 40, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(MATRIX_GREEN), 1))
        painter.drawRect(box_x + 20, input_y, input_width, 40)

        painter.setPen(QColor(MATRIX_GREEN))
        arrow = ">> " if self.parent_console.blink_state else "   "
        painter.drawText(box_x + 30, input_y, input_width - 20, 40,
                        Qt.AlignmentFlag.AlignVCenter,
                        f"{arrow}{self.input_text}")

        painter.setPen(QColor(MATRIX_DARK_GREEN))
        font.setPointSize(10)
        painter.setFont(font)

        state = self.parent_console.state
        if state == "wait_confirm":
            msg = "Press > to submit"
        elif state == "typing":
            msg = "Receiving access code..."
        else:
            msg = "Waiting for access code..."

        painter.drawText(box_x, box_y + 220, box_width, 40,
                        Qt.AlignmentFlag.AlignCenter, msg)

    def _draw_denied_screen(self, painter):
        box_width = 500
        box_height = 280
        box_x = (self.width() - box_width) // 2 - 100
        box_y = (self.height() - box_height) // 2

        painter.fillRect(box_x, box_y, box_width, box_height, QColor(15, 5, 5))

        pen = QPen(QColor(255, 30, 30), 3)
        painter.setPen(pen)
        painter.drawRect(box_x, box_y, box_width, box_height)

        header_height = 50
        painter.fillRect(box_x, box_y, box_width, header_height, QColor(200, 0, 0))
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Courier New", 18)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(box_x, box_y, box_width, header_height,
                        Qt.AlignmentFlag.AlignCenter, "ACCESS DENIED")

        painter.setPen(QColor(255, 80, 80))
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText(box_x + 20, box_y + 80, box_width - 40, 100,
                        Qt.TextFlag.TextWordWrap,
                        "Unauthorized access attempt detected.\n\nSystem locked indefinitely.\n\nIncident has been logged.")

        if self.parent_console.blink_state:
            painter.setPen(QColor(255, 50, 50))
            painter.drawText(box_x, box_y + 220, box_width, 40,
                           Qt.AlignmentFlag.AlignCenter, "[SYSTEM LOCKED]")

    def _draw_terminal(self, painter):
        margin = 40
        line_height = 22
        bottom_margin = 50

        font = QFont("Courier New", 13)
        painter.setFont(font)
        all_lines = []
        for prompt, cmd, output in self.terminal_history:
            all_lines.append(('cmd', f"{prompt}{cmd}"))
            if output:
                for line in output.split('\n'):
                    all_lines.append(('output', line))

        current_prompt = self.parent_console.console_system.get_prompt()
        cursor = "█" if self.parent_console.blink_state else " "
        current_line = f"{current_prompt}{self.parent_console.current_input}{cursor}"
        all_lines.append(('input', current_line))
        available_height = self.height() - margin - bottom_margin
        max_visible_lines = available_height // line_height

        #scroll_offset
        max_scroll = max(0, len(all_lines) - max_visible_lines)
        if self.scroll_offset > max_scroll:
            self.scroll_offset = max_scroll
        if len(all_lines) <= max_visible_lines:
            visible_lines = all_lines
        else:
            end_idx = len(all_lines) - self.scroll_offset
            start_idx = max(0, end_idx - max_visible_lines)
            visible_lines = all_lines[start_idx:end_idx]


        y = margin + 20
        for line_type, text in visible_lines:
            if line_type == 'cmd' or line_type == 'input':
                painter.setPen(QColor(MATRIX_GREEN))
            else:
                painter.setPen(QColor(MATRIX_DARK_GREEN))
            painter.drawText(margin, y, text)
            y += line_height

        # Индикатор прокрутки
        if self.scroll_offset > 0:
            painter.setPen(QColor(MATRIX_DARK_GREEN))
            painter.drawText(self.width() - 150, margin + 10, f"[scroll: -{self.scroll_offset}]")

    def sizeHint(self) -> QSize:
        return QSize(1000, 600)
