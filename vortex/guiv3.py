"""
Vortex GUI v3 - Modern live-coding studio with Save, Load, Clear, and Presets.
Version: v3 (Preserves v1 in versions/guiv1.py, v2 in versions/guiv2.py)
Created by Esperanza for Jack.
"""

import logging
import os
import signal
import sys
import time
from importlib import resources

from PyQt6.Qsci import (
    QsciLexerPython,
    QsciScintilla,
)
from PyQt6.QtCore import (
    QRunnable,
    Qt,
    QThreadPool,
    QTimer,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyleFactory,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from vortex import __version__, vortex_dsl

_logger = logging.getLogger(__name__)

DEFAULT_FONT_FAMILY = "Monospace"
SAVED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saved_beats")

# Curated musical presets for Jack
PRESETS = {
    "Select a Musical Preset...": "",
    "1. Classic 4-on-the-Floor Beat": '''p("drums", s(stack("bd*4", "[~ cp]*2", "hh*8"))
    >> speed("1")
    >> room(0.3)
    >> size(0.5)
)''',
    "2. Fast UK Jungle Amen Break": '''p("jungle", s("amencutup*8")
    >> speed("1 1.25 1.5 2")
    >> room(0.25)
)''',
    "3. Deep 808 Trap & Bounce": '''p("trap", s(stack("808bd*2", "[~ 808sd]", "[~ 808oh]*2", "808*4"))
    >> speed("1 0.9 1.1")
    >> room(0.3)
)''',
    "4. Ambient Sci-Fi Arpeggios": '''p("melody", s("arpy*8")
    >> speed("1 1.25 1.5 1.75 2")
    >> room(0.7)
    >> size(0.9)
)''',
    "5. Heavy Bass & Club Groove": '''# Channel 1: Driving drums
p("drums", s(stack("clubkick*4", "[~ realclaps]*2", "hh*8"))
    >> room(0.2)
)

# Channel 2: Funky Bassline
p("bass", s("bass1*4")
    >> speed("0.5 0.75 1 0.5")
    >> room(0.4)
)''',
}

INITIAL_CODE = '''# ==========================================================
# 🎵 Welcome to Vortex Studio v3!
# • Click [▶ Run Block] or press [Ctrl] + [Enter]
# • Click [🛑 Stop Sound (Hush)] to stop
# • [💾 Save] and [📂 Load] your beats anytime
# • Pick beats from the "Presets" dropdown above!
# ==========================================================

# 1. Acid House Beat
p("drums", s(stack("gabba*4", "cp*2").every(3, fast(2)))
    >> speed("1 1.2")
    >> room(0.35)
)

# 2. Jungle Amen Break
p("jungle", s("amencutup*8")
    >> speed("1 1.25 1.5 2")
    >> room(0.25)
)

# 3. Ambient Synth Arpeggio
p("synth", s("arpy*8")
    >> speed("1 1.25 1.5 1.75 2")
    >> room(0.7)
    >> size(0.9)
)

# Stop all sounds
hush()
'''


class HighlightLines(QRunnable):
    def __init__(self, editor, line_range, interval=0.15):
        super().__init__()
        self.editor = editor
        self.line_range = line_range
        self.interval = interval

    def run(self):
        time.sleep(self.interval)


class VortexStudioWindow(QMainWindow):
    def __init__(self, dsl_module):
        super().__init__()
        self._dsl_module = dsl_module
        self._font_size = 18
        self._current_file = None

        os.makedirs(SAVED_DIR, exist_ok=True)

        self.setWindowTitle(f"🎵 Vortex Studio {__version__} - Live Coding by Esperanza")
        self.resize(1280, 850)
        self.setMinimumSize(850, 600)

        # High-contrast dark styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #181825;
            }
            QWidget {
                color: #cdd6f4;
                font-family: 'Segoe UI', 'Ubuntu', 'Sans-serif';
            }
            QFrame#toolbar {
                background-color: #1e1e2e;
                border-bottom: 2px solid #313244;
                padding: 6px 10px;
            }
            QPushButton {
                font-weight: bold;
                font-size: 13px;
                padding: 7px 14px;
                border-radius: 6px;
                border: 1px solid transparent;
            }
            QPushButton#runBtn {
                background-color: #a6e3a1;
                color: #11111b;
            }
            QPushButton#runBtn:hover {
                background-color: #94e2d5;
            }
            QPushButton#stopBtn {
                background-color: #f38ba8;
                color: #11111b;
            }
            QPushButton#stopBtn:hover {
                background-color: #eba0ac;
            }
            QPushButton#saveBtn {
                background-color: #89b4fa;
                color: #11111b;
            }
            QPushButton#saveBtn:hover {
                background-color: #b4befe;
            }
            QPushButton#loadBtn {
                background-color: #f9e2af;
                color: #11111b;
            }
            QPushButton#loadBtn:hover {
                background-color: #f5c2e7;
            }
            QPushButton#clearBtn {
                background-color: #45475a;
                color: #f38ba8;
                border: 1px solid #585b70;
            }
            QPushButton#clearBtn:hover {
                background-color: #585b70;
                color: #ffffff;
            }
            QPushButton#toolBtn {
                background-color: #313244;
                color: #cdd6f4;
            }
            QPushButton#toolBtn:hover {
                background-color: #45475a;
            }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: bold;
                min-width: 220px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e2e;
                color: #cdd6f4;
                selection-background-color: #45475a;
                border: 1px solid #313244;
            }
            QTextEdit#console {
                background-color: #11111b;
                color: #a6e3a1;
                border: 1px solid #313244;
                border-radius: 6px;
                font-family: 'Monospace', 'Fira Code', 'DejaVu Sans Mono';
                font-size: 14px;
                padding: 8px;
            }
        """)

        # Central Layout
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top Toolbar
        toolbar = QFrame(self)
        toolbar.setObjectName("toolbar")
        tool_layout = QHBoxLayout(toolbar)
        tool_layout.setContentsMargins(10, 6, 10, 6)
        tool_layout.setSpacing(8)

        # 1. Run Button
        self.run_btn = QPushButton("▶ Run Block  (Ctrl+Enter)", self)
        self.run_btn.setObjectName("runBtn")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self.evaluate_block)
        tool_layout.addWidget(self.run_btn)

        # 2. Stop Button
        self.stop_btn = QPushButton("🛑 Stop Sound", self)
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.hush_sound)
        tool_layout.addWidget(self.stop_btn)

        tool_layout.addSpacing(10)

        # 3. Save Button
        self.save_btn = QPushButton("💾 Save", self)
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setToolTip("Save code to file (Ctrl+S)")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_file)
        tool_layout.addWidget(self.save_btn)

        # 4. Load Button
        self.load_btn = QPushButton("📂 Load", self)
        self.load_btn.setObjectName("loadBtn")
        self.load_btn.setToolTip("Load code from file (Ctrl+O)")
        self.load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_btn.clicked.connect(self.load_file)
        tool_layout.addWidget(self.load_btn)

        # 5. Clear Screen Button
        self.clear_btn = QPushButton("🗑 Clear", self)
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.setToolTip("Clear editor screen")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_screen)
        tool_layout.addWidget(self.clear_btn)

        tool_layout.addSpacing(10)

        # 6. Presets Dropdown
        self.preset_combo = QComboBox(self)
        for name in PRESETS.keys():
            self.preset_combo.addItem(name)
        self.preset_combo.currentIndexChanged.connect(self.load_preset)
        tool_layout.addWidget(self.preset_combo)

        tool_layout.addStretch()

        # Font zoom buttons
        font_down_btn = QPushButton("A-", self)
        font_down_btn.setObjectName("toolBtn")
        font_down_btn.setFixedWidth(36)
        font_down_btn.setToolTip("Smaller font")
        font_down_btn.clicked.connect(lambda: self.adjust_font_size(-2))
        tool_layout.addWidget(font_down_btn)

        font_up_btn = QPushButton("A+", self)
        font_up_btn.setObjectName("toolBtn")
        font_up_btn.setFixedWidth(36)
        font_up_btn.setToolTip("Larger font")
        font_up_btn.clicked.connect(lambda: self.adjust_font_size(+2))
        tool_layout.addWidget(font_up_btn)

        layout.addWidget(toolbar)

        # Vertical Splitter: Editor on top, Console on bottom
        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.setHandleWidth(4)

        # Scintilla Code Editor
        self._editor = QsciScintilla(self)
        self._editor.setText(INITIAL_CODE)
        self._editor.setUtf8(True)
        self._editor.setIndentationsUseTabs(False)
        self._editor.setAutoIndent(True)
        self._editor.setTabWidth(4)
        self._editor.setCaretWidth(3)
        self._editor.setCaretForegroundColor(QColor("#f5e0dc"))
        self._editor.setCaretLineVisible(True)
        self._editor.setCaretLineBackgroundColor(QColor("#24273a"))

        # Line numbers
        self._editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self._editor.setMarginWidth(0, "0000")
        self._editor.setMarginsBackgroundColor(QColor("#181825"))
        self._editor.setMarginsForegroundColor(QColor("#6c7086"))

        # Python Lexer
        self._lexer = QsciLexerPython(self._editor)
        self._editor_font = QFont(DEFAULT_FONT_FAMILY, self._font_size)
        self._editor_font.setStyleHint(QFont.StyleHint.Monospace)
        self._lexer.setFont(self._editor_font)

        # Syntax color palette
        self._lexer.setDefaultColor(QColor("#cdd6f4"))
        self._lexer.setDefaultPaper(QColor("#181825"))
        self._lexer.setColor(QColor("#6c7086"), QsciLexerPython.Comment)
        self._lexer.setColor(QColor("#6c7086"), QsciLexerPython.CommentBlock)
        self._lexer.setColor(QColor("#f9e2af"), QsciLexerPython.Number)
        self._lexer.setColor(QColor("#a6e3a1"), QsciLexerPython.DoubleQuotedString)
        self._lexer.setColor(QColor("#a6e3a1"), QsciLexerPython.SingleQuotedString)
        self._lexer.setColor(QColor("#cba6f7"), QsciLexerPython.Keyword)
        self._lexer.setColor(QColor("#89b4fa"), QsciLexerPython.FunctionMethodName)
        self._lexer.setColor(QColor("#fab387"), QsciLexerPython.Operator)
        self._editor.setLexer(self._lexer)

        splitter.addWidget(self._editor)

        # Console Panel
        console_panel = QFrame(self)
        console_layout = QVBoxLayout(console_panel)
        console_layout.setContentsMargins(10, 6, 10, 8)
        console_layout.setSpacing(4)

        console_header = QLabel("📡 Activity & Status Log:", console_panel)
        console_header.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 12px;")
        console_layout.addWidget(console_header)

        self.console = QTextEdit(console_panel)
        self.console.setObjectName("console")
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(130)
        self.console.append("✓ Vortex Studio v3 ready. Choose a block and click [▶ Run Block] or [Ctrl] + [Enter].")
        console_layout.addWidget(self.console)

        splitter.addWidget(console_panel)
        splitter.setSizes([670, 130])

        layout.addWidget(splitter)

        # Keyboard shortcuts
        QShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Return), self._editor).activated.connect(self.evaluate_block)
        QShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Enter), self._editor).activated.connect(self.evaluate_block)
        QShortcut(QKeySequence.StandardKey.Save, self).activated.connect(self.save_file)
        QShortcut(QKeySequence.StandardKey.Open, self).activated.connect(self.load_file)
        QShortcut(QKeySequence("Shift+Escape"), self).activated.connect(self.hush_sound)

        self.show()

    def adjust_font_size(self, delta):
        self._font_size = max(10, min(36, self._font_size + delta))
        self._editor_font.setPointSize(self._font_size)
        self._lexer.setFont(self._editor_font)
        self._editor.setLexer(self._lexer)
        self.log(f"Font size set to {self._font_size}pt")

    def log(self, message, is_error=False):
        color = "#f38ba8" if is_error else "#a6e3a1"
        self.console.append(f"<span style='color: {color};'>{message}</span>")
        self.console.verticalScrollBar().setValue(
            self.console.verticalScrollBar().maximum()
        )

    def save_file(self):
        default_path = self._current_file or os.path.join(SAVED_DIR, "my_beat.py")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Vortex Beat",
            default_path,
            "Python Files (*.py);;Text Files (*.txt);;All Files (*)",
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self._editor.text())
                self._current_file = file_path
                base_name = os.path.basename(file_path)
                self.setWindowTitle(f"🎵 Vortex Studio {__version__} - {base_name}")
                self.log(f"💾 <b>Saved:</b> <code>{file_path}</code>")
            except Exception as e:
                self.log(f"⚠️ Error saving file: {e}", is_error=True)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Vortex Beat",
            SAVED_DIR,
            "Python Files (*.py);;Text Files (*.txt);;All Files (*)",
        )
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._editor.setText(content)
                self._current_file = file_path
                base_name = os.path.basename(file_path)
                self.setWindowTitle(f"🎵 Vortex Studio {__version__} - {base_name}")
                self.log(f"📂 <b>Loaded:</b> <code>{file_path}</code>")
            except Exception as e:
                self.log(f"⚠️ Error loading file: {e}", is_error=True)

    def clear_screen(self):
        # If there is meaningful code, prompt so Jack doesn't lose anything accidentally
        if len(self._editor.text().strip()) > 50:
            reply = QMessageBox.question(
                self,
                "Clear Editor?",
                "Are you sure you want to clear the editor screen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._editor.setText("")
        self._current_file = None
        self.setWindowTitle(f"🎵 Vortex Studio {__version__} - Live Coding by Esperanza")
        self.log("🗑 <b>Editor cleared.</b> Blank canvas ready!")

    def load_preset(self, index):
        name = self.preset_combo.currentText()
        code = PRESETS.get(name)
        if code:
            self._editor.append("\n\n" + code)
            self.log(f"Added preset: <b>{name}</b> (scrolled to bottom)")
            self._editor.setCursorPosition(self._editor.lines(), 0)

    def hush_sound(self):
        try:
            hush_func = getattr(self._dsl_module, "hush", None)
            if hush_func:
                hush_func()
            self.log("🛑 <b>HUSH</b>: All streams silenced.")
        except Exception as e:
            self.log(f"Error executing hush: {e}", is_error=True)

    def get_current_block(self):
        # 1. If user selected text with mouse, evaluate that exact selection!
        if self._editor.hasSelectedText():
            selected = self._editor.selectedText().strip()
            return selected, None

        # 2. Intelligently extract block surrounding cursor between blank lines
        text = self._editor.text()
        lines = text.splitlines()
        line, _ = self._editor.getCursorPosition()

        if line >= len(lines) or not lines[line].strip():
            return "", None

        start_line = 0
        for i in range(line - 1, -1, -1):
            if not lines[i].strip():
                start_line = i + 1
                break

        end_line = len(lines) - 1
        for i in range(line + 1, len(lines)):
            if not lines[i].strip():
                end_line = i - 1
                break

        block = "\n".join(lines[start_line : end_line + 1]).strip()
        return block, (start_line, end_line)

    def evaluate_block(self):
        code, span = self.get_current_block()
        if not code:
            self.log("⚠️ No code block found at cursor position. Click inside a block first.", is_error=True)
            return

        first_line = code.split("\n")[0][:45]
        self.log(f"▶ <b>Running:</b> <code>{first_line}...</code>")

        try:
            exec(code, vars(self._dsl_module))
            if span:
                self.highlight_block(span[0], span[1])
        except Exception as e:
            self.log(f"⚠️ <b>Execution Error:</b> {e}", is_error=True)

    def highlight_block(self, start_line, end_line):
        pool = QThreadPool.globalInstance()
        runnable = HighlightLines(self._editor, (start_line, end_line))
        pool.start(runnable)


def start_guiv3():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create("Fusion"))

    sig_timer = QTimer()
    sig_timer.timeout.connect(lambda: None)
    sig_timer.start(200)

    with vortex_dsl() as module:
        window = VortexStudioWindow(dsl_module=module)
        app.exec()


if __name__ == "__main__":
    start_guiv3()
