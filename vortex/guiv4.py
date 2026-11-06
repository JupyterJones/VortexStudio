"""
Vortex GUI v4 - Live Coding Music Studio with Live MP3 Recording & Playback.
Version: v4 (Preserves v1 in versions/guiv1.py, v2 in versions/guiv2.py, v3 in versions/guiv3.py)
Created by Esperanza for Jack.
"""

import datetime
import logging
import os
import signal
import subprocess
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
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVED_DIR = os.path.join(BASE_DIR, "saved_beats")
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")

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
# 🎵 Welcome to Vortex Studio v4!
# • Click [▶ Run Block] or press [Ctrl] + [Enter]
# • Click [🛑 Stop Sound] to hush
# • [⏺ Record MP3] to record live to MP3
# • [▶ Play MP3] & [📂 Load MP3] to listen back anytime
# • [💾 Save] and [📂 Load] your code scripts
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

        # Recording state
        self._is_recording = False
        self._record_proc = None
        self._record_start_time = 0
        self._temp_mp3_path = None

        # MP3 Playback state
        self._current_mp3_path = None
        self._play_proc = None

        os.makedirs(SAVED_DIR, exist_ok=True)
        os.makedirs(RECORDINGS_DIR, exist_ok=True)

        self.setWindowTitle(f"🎵 Vortex Studio {__version__} - Live Coding by Esperanza")
        self.resize(1380, 880)
        self.setMinimumSize(920, 620)

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
                padding: 7px 12px;
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
            QPushButton#recBtn {
                background-color: #f38ba8;
                color: #11111b;
            }
            QPushButton#recBtn:hover {
                background-color: #ff5555;
            }
            QPushButton#playMp3Btn {
                background-color: #a6e3a1;
                color: #11111b;
            }
            QPushButton#playMp3Btn:hover {
                background-color: #85d7bb;
            }
            QPushButton#stopMp3Btn {
                background-color: #f9e2af;
                color: #11111b;
            }
            QPushButton#loadMp3Btn {
                background-color: #313244;
                color: #89b4fa;
                border: 1px solid #45475a;
            }
            QPushButton#loadMp3Btn:hover {
                background-color: #45475a;
                color: #b4befe;
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
                background-color: #313244;
                color: #eba0ac;
                border: 1px solid #45475a;
            }
            QPushButton#clearBtn:hover {
                background-color: #45475a;
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
                padding: 6px 10px;
                font-size: 13px;
                font-weight: bold;
                min-width: 200px;
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
        tool_layout.setSpacing(6)

        # 1. Run Button
        self.run_btn = QPushButton("▶ Run (Ctrl+Enter)", self)
        self.run_btn.setObjectName("runBtn")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self.evaluate_block)
        tool_layout.addWidget(self.run_btn)

        # 2. Stop Button
        self.stop_btn = QPushButton("🛑 Stop", self)
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.hush_sound)
        tool_layout.addWidget(self.stop_btn)

        tool_layout.addSpacing(6)

        # 3. RECORD MP3 Button
        self.rec_btn = QPushButton("⏺ Record MP3", self)
        self.rec_btn.setObjectName("recBtn")
        self.rec_btn.setToolTip("Record live audio output directly to MP3 file")
        self.rec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rec_btn.clicked.connect(self.toggle_recording)
        tool_layout.addWidget(self.rec_btn)

        # 4. PLAY MP3 Button
        self.play_mp3_btn = QPushButton("▶ Play MP3", self)
        self.play_mp3_btn.setObjectName("playMp3Btn")
        self.play_mp3_btn.setToolTip("Play back recorded or loaded MP3")
        self.play_mp3_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_mp3_btn.clicked.connect(self.toggle_play_mp3)
        tool_layout.addWidget(self.play_mp3_btn)

        # 5. LOAD MP3 Button
        self.load_mp3_btn = QPushButton("📂 Load MP3", self)
        self.load_mp3_btn.setObjectName("loadMp3Btn")
        self.load_mp3_btn.setToolTip("Select an existing MP3 file to play")
        self.load_mp3_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_mp3_btn.clicked.connect(self.load_mp3)
        tool_layout.addWidget(self.load_mp3_btn)

        tool_layout.addSpacing(6)

        # 6. Save Script Button
        self.save_btn = QPushButton("💾 Save", self)
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setToolTip("Save code script (Ctrl+S)")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_file)
        tool_layout.addWidget(self.save_btn)

        # 7. Load Script Button
        self.load_btn = QPushButton("📂 Load", self)
        self.load_btn.setObjectName("loadBtn")
        self.load_btn.setToolTip("Load code script (Ctrl+O)")
        self.load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_btn.clicked.connect(self.load_file)
        tool_layout.addWidget(self.load_btn)

        # 8. Clear Screen Button
        self.clear_btn = QPushButton("🗑 Clear", self)
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.setToolTip("Clear editor screen")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_screen)
        tool_layout.addWidget(self.clear_btn)

        tool_layout.addSpacing(6)

        # 9. Presets Dropdown
        self.preset_combo = QComboBox(self)
        for name in PRESETS.keys():
            self.preset_combo.addItem(name)
        self.preset_combo.currentIndexChanged.connect(self.load_preset)
        tool_layout.addWidget(self.preset_combo)

        tool_layout.addStretch()

        # Font zoom buttons
        font_down_btn = QPushButton("A-", self)
        font_down_btn.setObjectName("toolBtn")
        font_down_btn.setFixedWidth(32)
        font_down_btn.clicked.connect(lambda: self.adjust_font_size(-2))
        tool_layout.addWidget(font_down_btn)

        font_up_btn = QPushButton("A+", self)
        font_up_btn.setObjectName("toolBtn")
        font_up_btn.setFixedWidth(32)
        font_up_btn.clicked.connect(lambda: self.adjust_font_size(+2))
        tool_layout.addWidget(font_up_btn)

        layout.addWidget(toolbar)

        # Splitter: Editor on top, Console on bottom
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
        self.console.append("✓ Vortex Studio v4 ready. Click [⏺ Record MP3] to capture, [▶ Play MP3] to listen back!")
        console_layout.addWidget(self.console)

        splitter.addWidget(console_panel)
        splitter.setSizes([670, 130])

        layout.addWidget(splitter)

        # Recording timer
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update_recording_timer)

        # Playback poll timer to detect when mp3 finished playing
        self._play_timer = QTimer(self)
        self._play_timer.setInterval(500)
        self._play_timer.timeout.connect(self._check_playback_finished)

        # Keyboard shortcuts
        QShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Return), self._editor).activated.connect(self.evaluate_block)
        QShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Enter), self._editor).activated.connect(self.evaluate_block)
        QShortcut(QKeySequence.StandardKey.Save, self).activated.connect(self.save_file)
        QShortcut(QKeySequence.StandardKey.Open, self).activated.connect(self.load_file)
        QShortcut(QKeySequence("Shift+Escape"), self).activated.connect(self.hush_sound)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.toggle_recording)

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

    # ==================== MP3 RECORDING ====================

    def toggle_recording(self):
        if not self._is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._temp_mp3_path = os.path.join(RECORDINGS_DIR, f"vortex_jam_{timestamp_str}.mp3")

        ffmpeg_bin = "/usr/local/bin/ffmpeg"
        if not os.path.exists(ffmpeg_bin):
            ffmpeg_bin = "ffmpeg"

        cmd = [
            ffmpeg_bin,
            "-y",
            "-f", "pulse",
            "-i", "default.monitor",
            "-b:a", "192k",
            self._temp_mp3_path,
        ]

        try:
            self._record_proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._is_recording = True
            self._record_start_time = time.time()
            self._timer.start()

            self.rec_btn.setStyleSheet("background-color: #ff0055; color: #ffffff; border: 2px solid #ffffff;")
            self.rec_btn.setText("⏹ Stop REC (00:00)")
            self.log(f"🔴 <b>RECORDING STARTED:</b> Capturing live audio to MP3...")
        except Exception as e:
            self.log(f"⚠️ Failed to start MP3 recording: {e}", is_error=True)

    def _update_recording_timer(self):
        if self._is_recording:
            elapsed = int(time.time() - self._record_start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            self.rec_btn.setText(f"⏹ Stop REC ({mins:02d}:{secs:02d})")

    def stop_recording(self):
        if not self._is_recording:
            return

        self._timer.stop()
        self._is_recording = False
        self.rec_btn.setStyleSheet("")
        self.rec_btn.setText("⏺ Record MP3")

        if self._record_proc:
            try:
                self._record_proc.communicate(input=b"q", timeout=3)
            except Exception:
                try:
                    self._record_proc.send_signal(signal.SIGINT)
                    self._record_proc.wait(timeout=2)
                except Exception:
                    self._record_proc.kill()
            self._record_proc = None

        if os.path.exists(self._temp_mp3_path) and os.path.getsize(self._temp_mp3_path) > 1000:
            file_size_kb = os.path.getsize(self._temp_mp3_path) / 1024
            base_name = os.path.basename(self._temp_mp3_path)
            self._current_mp3_path = self._temp_mp3_path
            self.play_mp3_btn.setText(f"▶ Play: {base_name[:12]}...")

            self.log(f"🎉 <b>RECORDING SAVED!</b> <code>{base_name}</code> ({file_size_kb:.1f} KB)")
            self.log(f"📁 Path: <code>{self._temp_mp3_path}</code>")
            self.log("💡 Click <b>[▶ Play MP3]</b> to listen to what you just recorded!")

            # Ask user if they want to Save As
            reply = QMessageBox.question(
                self,
                "MP3 Saved!",
                f"Your recording was saved as:\n\n{base_name}\n({file_size_kb:.1f} KB)\n\nWould you like to Save As a custom filename?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                custom_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save MP3 Recording As",
                    self._temp_mp3_path,
                    "MP3 Audio (*.mp3)",
                )
                if custom_path and custom_path != self._temp_mp3_path:
                    try:
                        os.rename(self._temp_mp3_path, custom_path)
                        self._current_mp3_path = custom_path
                        new_base = os.path.basename(custom_path)
                        self.play_mp3_btn.setText(f"▶ Play: {new_base[:12]}...")
                        self.log(f"💾 Renamed recording to: <code>{new_base}</code>")
                    except Exception as e:
                        self.log(f"⚠️ Error renaming MP3: {e}", is_error=True)
        else:
            self.log("⚠️ Recording was too short or empty.", is_error=True)

    # ==================== MP3 PLAYBACK ====================

    def load_mp3(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select MP3 File to Play",
            RECORDINGS_DIR,
            "MP3 Audio (*.mp3);;All Audio (*.mp3 *.wav *.ogg *.flac);;All Files (*)",
        )
        if file_path and os.path.exists(file_path):
            self._current_mp3_path = file_path
            base_name = os.path.basename(file_path)
            self.play_mp3_btn.setText(f"▶ Play: {base_name[:12]}...")
            self.log(f"🎵 <b>Loaded MP3:</b> <code>{base_name}</code>. Click [▶ Play MP3] to listen!")

    def toggle_play_mp3(self):
        if self._play_proc is not None:
            self.stop_play_mp3()
        else:
            self.start_play_mp3()

    def start_play_mp3(self):
        # If no MP3 loaded, ask user to select one
        if not self._current_mp3_path or not os.path.exists(self._current_mp3_path):
            self.load_mp3()
            if not self._current_mp3_path:
                return

        try:
            # pw-play is the native PipeWire player
            self._play_proc = subprocess.Popen(
                ["pw-play", self._current_mp3_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            base_name = os.path.basename(self._current_mp3_path)
            self.play_mp3_btn.setText("⏹ Stop MP3")
            self.play_mp3_btn.setObjectName("stopMp3Btn")
            self.play_mp3_btn.setStyleSheet("background-color: #f9e2af; color: #11111b;")
            self.log(f"▶ <b>Playing MP3:</b> <code>{base_name}</code>")
            self._play_timer.start()
        except Exception as e:
            self.log(f"⚠️ Error playing MP3: {e}", is_error=True)
            self.stop_play_mp3()

    def stop_play_mp3(self):
        self._play_timer.stop()
        if self._play_proc is not None:
            try:
                self._play_proc.terminate()
                self._play_proc.wait(timeout=1)
            except Exception:
                try:
                    self._play_proc.kill()
                except Exception:
                    pass
            self._play_proc = None

        self.play_mp3_btn.setObjectName("playMp3Btn")
        self.play_mp3_btn.setStyleSheet("")
        if self._current_mp3_path:
            base_name = os.path.basename(self._current_mp3_path)
            self.play_mp3_btn.setText(f"▶ Play: {base_name[:12]}...")
        else:
            self.play_mp3_btn.setText("▶ Play MP3")
        self.log("⏹ MP3 playback stopped.")

    def _check_playback_finished(self):
        if self._play_proc is not None:
            ret = self._play_proc.poll()
            if ret is not None:
                # Process finished on its own
                self.stop_play_mp3()

    def closeEvent(self, event):
        if self._is_recording:
            self.stop_recording()
        if self._play_proc is not None:
            self.stop_play_mp3()
        super().closeEvent(event)

    # ==================== SCRIPT SAVE / LOAD / CLEAR ====================

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
                self.log(f"💾 <b>Saved script:</b> <code>{file_path}</code>")
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
                self.log(f"📂 <b>Loaded script:</b> <code>{file_path}</code>")
            except Exception as e:
                self.log(f"⚠️ Error loading file: {e}", is_error=True)

    def clear_screen(self):
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
            self.log("🛑 <b>HUSH</b>: All live streams silenced.")
        except Exception as e:
            self.log(f"Error executing hush: {e}", is_error=True)

    def get_current_block(self):
        if self._editor.hasSelectedText():
            selected = self._editor.selectedText().strip()
            return selected, None

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


def start_guiv4():
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
    start_guiv4()
