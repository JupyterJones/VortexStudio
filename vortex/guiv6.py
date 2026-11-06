"""
Vortex GUI v6 - Advanced Live Coding Music Studio with Dedicated Beat Notes Scratchpad & Live MP3 Suite.
Created by Jack Northrup and Esperanza AI Companion.
Version: v6 (Preserves v1, v2, v3, v4, v5 in versions/)
"""

import datetime
import logging
import os
import signal
import subprocess
import sys
import time

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
    QStatusBar,
    QStyleFactory,
    QTabWidget,
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
NOTES_DIR = os.path.join(BASE_DIR, "beat_notes")

# Curated musical presets for Jack
PRESETS = {
    "Select a Musical Preset...": "",
    "1. Acid House 303 Groove": '''p("drums", s(stack("gabba*4", "cp*2").every(3, fast(2)))
    >> speed("1 1.2")
    >> room(0.35)
)

p("acid", s("bass1*8")
    >> speed("0.8 1 1.2 0.9")
    >> room(0.4)
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
# 🎵 Vortex Studio v6 — by Jack Northrup & Esperanza AI Companion
# • Click [▶ Run (Ctrl+Enter)] or press Ctrl+Enter on any block
# • Click [🛑 Stop] to hush all sounds
# • [💾 Save] to quick-save / [💾 Save As] for a custom name
# • [📂 Load Script] to open your saved .py beat files
# • [⏺ Record MP3] to capture live / [▶ Play MP3] to listen back
# • [Remove Line #s] / [Show Line #s] to toggle line numbers
# • Use the spacious "📝 Beat Notes" area below to store recipes,
#   read notes, and copy/paste snippets right up into the editor!
# ==========================================================

# 1. Acid House Driving Groove
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

INITIAL_NOTES = '''# ==========================================================
# 📝 JACK NORTHRUP'S BEAT RECIPES & SCRATCHPAD
# Co-created with Esperanza AI Companion
# • Read and edit your notes, ideas, comments, and beat recipes.
# • Select any snippet and click [⬆ Insert into Code] to paste it above!
# • Or click [▶ Run Note Selection] to hear it instantly!
# • [💾 Save Notes] / [💾 Save Notes As...] saves directly to beat_notes/
# ==========================================================

# --- FAVORITE DRUM RECIPES ---
# Driving Acid House:
p("drums", s(stack("gabba*4", "cp*2").every(3, fast(2))) >> speed("1 1.2") >> room(0.35))

# Funky Club Kick & Claps:
p("drums", s(stack("clubkick*4", "[~ realclaps]*2", "hh*8")) >> room(0.2))

# 808 Trap Roll:
p("trap", s(stack("808bd*2", "[~ 808sd]", "[~ 808oh]*2", "808*4")) >> speed("1 0.95") >> room(0.3))

# Fast Jungle Amen:
p("jungle", s("amencutup*8") >> speed("1 1.25 1.5 2") >> room(0.25))

# --- SYNTH & MELODY RECIPES ---
# Sci-Fi Glitch Arp:
p("synth", s("arpy*8") >> speed("1 1.25 1.5 1.75 2") >> room(0.7) >> size(0.9))

# Deep Sub Bass:
p("bass", s("bass1*4") >> speed("0.5 0.75 1 0.5") >> room(0.4))

# Ethereal Vowel Filter Pad:
p("pad", s("birds*4") >> speed("0.5 1 0.75") >> vowel("a o e i") >> room(0.8))

# --- MY COMMENTS & PRODUCTION LOG ---
# [2026-11-06] The amencutup sample sliced at speed 1.5 makes a sick drum & bass drop.
# Try stacking realclaps with gabba kicks on the 3rd beat.
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
        self._font_size = 17
        self._current_file = None
        self._show_line_numbers = True
        self._notes_current_file = os.path.join(NOTES_DIR, "my_favorite_beats.txt")

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
        os.makedirs(NOTES_DIR, exist_ok=True)

        self.setWindowTitle(f"🎵 Vortex Studio {__version__} — by Jack Northrup & Esperanza AI Companion [Untitled]")
        self.resize(1440, 920)
        self.setMinimumSize(960, 640)

        # High-contrast dark styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #181825;
            }
            QWidget {
                color: #cdd6f4;
                font-family: 'Segoe UI', 'Ubuntu', 'Sans-serif';
            }
            QFrame#mainToolbar {
                background-color: #1e1e2e;
                border-bottom: 2px solid #313244;
                padding: 6px 10px;
            }
            QFrame#notesToolbar {
                background-color: #1e1e2e;
                border-bottom: 1px solid #313244;
                padding: 4px 8px;
            }
            QPushButton {
                font-weight: bold;
                font-size: 13px;
                padding: 6px 12px;
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
            QPushButton#saveAsBtn {
                background-color: #74c7ec;
                color: #11111b;
            }
            QPushButton#saveAsBtn:hover {
                background-color: #89dceb;
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
            QPushButton#notesActionBtn {
                background-color: #cba6f7;
                color: #11111b;
            }
            QPushButton#notesActionBtn:hover {
                background-color: #f5c2e7;
            }
            QPushButton#notesRunBtn {
                background-color: #a6e3a1;
                color: #11111b;
            }
            QPushButton#notesRunBtn:hover {
                background-color: #94e2d5;
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
                min-width: 190px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e2e;
                color: #cdd6f4;
                selection-background-color: #45475a;
                border: 1px solid #313244;
            }
            QTabWidget::pane {
                border: 1px solid #313244;
                background-color: #181825;
            }
            QTabBar::tab {
                background-color: #1e1e2e;
                color: #a6adc8;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #313244;
                color: #89b4fa;
                border-bottom: 2px solid #89b4fa;
            }
            QTabBar::tab:hover {
                background-color: #252538;
                color: #cdd6f4;
            }
            QTextEdit#console {
                background-color: #11111b;
                color: #a6e3a1;
                border: 1px solid #313244;
                border-radius: 4px;
                font-family: 'Monospace', 'Fira Code', 'DejaVu Sans Mono';
                font-size: 13px;
                padding: 8px;
            }
            QStatusBar {
                background-color: #11111b;
                color: #89b4fa;
                font-size: 12px;
                border-top: 1px solid #313244;
            }
        """)

        # Central Widget & Vertical Layout
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ----------------- TOP MAIN TOOLBAR -----------------
        main_toolbar = QFrame(self)
        main_toolbar.setObjectName("mainToolbar")
        tool_layout = QHBoxLayout(main_toolbar)
        tool_layout.setContentsMargins(10, 6, 10, 6)
        tool_layout.setSpacing(6)

        # 1. Run Button
        self.run_btn = QPushButton("▶ Run (Ctrl+Enter)", self)
        self.run_btn.setObjectName("runBtn")
        self.run_btn.setToolTip("Execute the current code block or selection in the live audio engine")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self.evaluate_block)
        tool_layout.addWidget(self.run_btn)

        # 2. Stop Button
        self.stop_btn = QPushButton("🛑 Stop", self)
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setToolTip("Hush and silence all running audio streams (Shift+Escape)")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.hush_sound)
        tool_layout.addWidget(self.stop_btn)

        tool_layout.addSpacing(6)

        # 3. MP3 Recording
        self.rec_btn = QPushButton("⏺ Record MP3", self)
        self.rec_btn.setObjectName("recBtn")
        self.rec_btn.setToolTip("Record live audio output directly to MP3 file (Ctrl+R)")
        self.rec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rec_btn.clicked.connect(self.toggle_recording)
        tool_layout.addWidget(self.rec_btn)

        # 4. MP3 Play
        self.play_mp3_btn = QPushButton("▶ Play MP3", self)
        self.play_mp3_btn.setObjectName("playMp3Btn")
        self.play_mp3_btn.setToolTip("Play back recorded or loaded MP3 via PipeWire")
        self.play_mp3_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_mp3_btn.clicked.connect(self.toggle_play_mp3)
        tool_layout.addWidget(self.play_mp3_btn)

        # 5. MP3 Load
        self.load_mp3_btn = QPushButton("📂 Load MP3", self)
        self.load_mp3_btn.setObjectName("loadMp3Btn")
        self.load_mp3_btn.setToolTip("Select an existing MP3 file from recordings to play")
        self.load_mp3_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_mp3_btn.clicked.connect(self.load_mp3)
        tool_layout.addWidget(self.load_mp3_btn)

        tool_layout.addSpacing(6)

        # 6. Save Script (Quick Save)
        self.save_btn = QPushButton("💾 Save", self)
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setToolTip("Quick-save current script file (Ctrl+S)")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_file)
        tool_layout.addWidget(self.save_btn)

        # 7. Save Script As
        self.save_as_btn = QPushButton("💾 Save As", self)
        self.save_as_btn.setObjectName("saveAsBtn")
        self.save_as_btn.setToolTip("Save current script under a new filename (Ctrl+Shift+S)")
        self.save_as_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_as_btn.clicked.connect(self.save_file_as)
        tool_layout.addWidget(self.save_as_btn)

        # 8. Load Script
        self.load_btn = QPushButton("📂 Load Script", self)
        self.load_btn.setObjectName("loadBtn")
        self.load_btn.setToolTip("Load an existing Python beat script to edit and play (Ctrl+O)")
        self.load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_btn.clicked.connect(self.load_file)
        tool_layout.addWidget(self.load_btn)

        # 9. Clear Screen
        self.clear_btn = QPushButton("🗑 Clear", self)
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.setToolTip("Clear the main editor screen for a fresh canvas")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_screen)
        tool_layout.addWidget(self.clear_btn)

        tool_layout.addSpacing(6)

        # 10. Presets Dropdown
        self.preset_combo = QComboBox(self)
        for name in PRESETS.keys():
            self.preset_combo.addItem(name)
        self.preset_combo.currentIndexChanged.connect(self.load_preset)
        tool_layout.addWidget(self.preset_combo)

        tool_layout.addStretch()

        # Font Zoom Controls
        font_down_btn = QPushButton("A-", self)
        font_down_btn.setObjectName("toolBtn")
        font_down_btn.setFixedWidth(32)
        font_down_btn.setToolTip("Decrease editor font size")
        font_down_btn.clicked.connect(lambda: self.adjust_font_size(-2))
        tool_layout.addWidget(font_down_btn)

        font_up_btn = QPushButton("A+", self)
        font_up_btn.setObjectName("toolBtn")
        font_up_btn.setFixedWidth(32)
        font_up_btn.setToolTip("Increase editor font size")
        font_up_btn.clicked.connect(lambda: self.adjust_font_size(+2))
        tool_layout.addWidget(font_up_btn)

        tool_layout.addSpacing(4)

        # 11. Remove / Show Line Numbers Toggle Button
        self.line_num_btn = QPushButton("Remove Line #s", self)
        self.line_num_btn.setObjectName("toolBtn")
        self.line_num_btn.setToolTip("Click to remove or restore line numbers (Ctrl+L)")
        self.line_num_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.line_num_btn.clicked.connect(self.toggle_line_numbers)
        tool_layout.addWidget(self.line_num_btn)

        main_layout.addWidget(main_toolbar)

        # ----------------- MAIN VERTICAL SPLITTER -----------------
        # Splitter divides Top (Main Editor) and Bottom (Beat Notes & Log)
        self.splitter = QSplitter(Qt.Orientation.Vertical, self)
        self.splitter.setHandleWidth(5)

        # --- TOP PANE: Main Code Editor ---
        top_container = QWidget(self)
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(10, 6, 10, 4)
        top_layout.setSpacing(4)

        top_header_layout = QHBoxLayout()
        top_header_label = QLabel("🎹 Main Beat Code Editor (Python / Vortex DSL):", top_container)
        top_header_label.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 13px;")
        top_header_layout.addWidget(top_header_label)

        self.file_badge = QLabel("[Untitled Script]", top_container)
        self.file_badge.setStyleSheet("color: #fab387; font-weight: bold; font-size: 12px; background: #313244; padding: 2px 8px; border-radius: 4px;")
        top_header_layout.addWidget(self.file_badge)
        top_header_layout.addStretch()

        hint_label = QLabel("Tip: Click inside any block and press Ctrl+Enter to run", top_container)
        hint_label.setStyleSheet("color: #6c7086; font-size: 11px;")
        top_header_layout.addWidget(hint_label)

        top_layout.addLayout(top_header_layout)

        # Scintilla Code Editor
        self._editor = QsciScintilla(top_container)
        self._editor.setText(INITIAL_CODE)
        self._editor.setUtf8(True)
        self._editor.setIndentationsUseTabs(False)
        self._editor.setAutoIndent(True)
        self._editor.setTabWidth(4)
        self._editor.setCaretWidth(3)
        self._editor.setCaretForegroundColor(QColor("#f5e0dc"))
        self._editor.setCaretLineVisible(True)
        self._editor.setCaretLineBackgroundColor(QColor("#24273a"))

        # Margin 0: Line numbers
        self._editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self._editor.setMarginWidth(0, "0000")
        self._editor.setMarginsBackgroundColor(QColor("#181825"))
        self._editor.setMarginsForegroundColor(QColor("#6c7086"))

        # Python Lexer for Top Editor
        self._lexer = QsciLexerPython(self._editor)
        self._editor_font = QFont(DEFAULT_FONT_FAMILY, self._font_size)
        self._editor_font.setStyleHint(QFont.StyleHint.Monospace)
        self._lexer.setFont(self._editor_font)

        self._configure_lexer_colors(self._lexer)
        self._editor.setLexer(self._lexer)
        top_layout.addWidget(self._editor)

        self.splitter.addWidget(top_container)

        # --- BOTTOM PANE: Spacious Tabbed Area (Beat Notes & Log) ---
        bottom_container = QWidget(self)
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(10, 4, 10, 6)
        bottom_layout.setSpacing(4)

        self.tabs = QTabWidget(bottom_container)

        # Tab 1: 📝 Beat Notes & Pattern Library Scratchpad
        notes_tab = QWidget()
        notes_tab_layout = QVBoxLayout(notes_tab)
        notes_tab_layout.setContentsMargins(0, 4, 0, 0)
        notes_tab_layout.setSpacing(4)

        # Notes Sub-Toolbar
        notes_toolbar = QFrame(notes_tab)
        notes_toolbar.setObjectName("notesToolbar")
        notes_tool_layout = QHBoxLayout(notes_toolbar)
        notes_tool_layout.setContentsMargins(6, 4, 6, 4)
        notes_tool_layout.setSpacing(6)

        notes_title = QLabel("📝 Beat Notes & Scratchpad:", notes_toolbar)
        notes_title.setStyleSheet("color: #cba6f7; font-weight: bold; font-size: 12px;")
        notes_tool_layout.addWidget(notes_title)

        self.notes_file_badge = QLabel("[my_favorite_beats.txt]", notes_toolbar)
        self.notes_file_badge.setStyleSheet("color: #f9e2af; font-weight: bold; font-size: 11px; background: #313244; padding: 2px 6px; border-radius: 4px;")
        notes_tool_layout.addWidget(self.notes_file_badge)

        notes_tool_layout.addSpacing(10)

        # Notes Load Button
        load_notes_btn = QPushButton("📂 Load Notes (.txt)", notes_toolbar)
        load_notes_btn.setObjectName("loadMp3Btn")
        load_notes_btn.setToolTip("Open a beat recipe notes file (.txt)")
        load_notes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        load_notes_btn.clicked.connect(self.load_notes_file)
        notes_tool_layout.addWidget(load_notes_btn)

        # Notes Save Button
        save_notes_btn = QPushButton("💾 Save Notes", notes_toolbar)
        save_notes_btn.setObjectName("saveBtn")
        save_notes_btn.setToolTip("Quick-save current beat notes & comments to file")
        save_notes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_notes_btn.clicked.connect(self.save_notes)
        notes_tool_layout.addWidget(save_notes_btn)

        # Notes Save As Button
        save_notes_as_btn = QPushButton("💾 Save Notes As...", notes_toolbar)
        save_notes_as_btn.setObjectName("saveAsBtn")
        save_notes_as_btn.setToolTip("Save notes with a custom filename in beat_notes/")
        save_notes_as_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_notes_as_btn.clicked.connect(self.save_notes_as)
        notes_tool_layout.addWidget(save_notes_as_btn)

        notes_tool_layout.addSpacing(10)

        # Insert Selected snippet into main editor
        insert_btn = QPushButton("⬆ Insert into Code", notes_toolbar)
        insert_btn.setObjectName("notesActionBtn")
        insert_btn.setToolTip("Copy highlighted beat snippet directly into the main code editor at cursor")
        insert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        insert_btn.clicked.connect(self.insert_selected_note_into_editor)
        notes_tool_layout.addWidget(insert_btn)

        # Run Selected snippet directly
        run_note_btn = QPushButton("▶ Run Note Selection", notes_toolbar)
        run_note_btn.setObjectName("notesRunBtn")
        run_note_btn.setToolTip("Evaluate highlighted beat recipe line immediately without needing to paste")
        run_note_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        run_note_btn.clicked.connect(self.run_selected_note)
        notes_tool_layout.addWidget(run_note_btn)

        notes_tool_layout.addStretch()

        clear_notes_btn = QPushButton("🗑 Clear Notes", notes_toolbar)
        clear_notes_btn.setObjectName("clearBtn")
        clear_notes_btn.setToolTip("Clear notes scratchpad")
        clear_notes_btn.clicked.connect(self.clear_notes)
        notes_tool_layout.addWidget(clear_notes_btn)

        notes_tab_layout.addWidget(notes_toolbar)

        # Notes Scintilla Editor (high contrast, line numbers, monospace)
        self._notes_editor = QsciScintilla(notes_tab)
        # Load existing notes if file exists, otherwise initial template
        initial_notes_content = INITIAL_NOTES
        if os.path.exists(self._notes_current_file):
            try:
                with open(self._notes_current_file, "r", encoding="utf-8") as f:
                    file_txt = f.read().strip()
                    if file_txt:
                        initial_notes_content = file_txt
            except Exception:
                pass
        self._notes_editor.setText(initial_notes_content)
        self._notes_editor.setUtf8(True)
        self._notes_editor.setIndentationsUseTabs(False)
        self._notes_editor.setAutoIndent(True)
        self._notes_editor.setTabWidth(4)
        self._notes_editor.setCaretWidth(2)
        self._notes_editor.setCaretForegroundColor(QColor("#f5e0dc"))
        self._notes_editor.setCaretLineVisible(True)
        self._notes_editor.setCaretLineBackgroundColor(QColor("#24273a"))

        # Line numbers on notes
        self._notes_editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self._notes_editor.setMarginWidth(0, "000")
        self._notes_editor.setMarginsBackgroundColor(QColor("#181825"))
        self._notes_editor.setMarginsForegroundColor(QColor("#585b70"))

        # Lexer for notes (Python lexer highlights comments `#`, strings, commands cleanly)
        self._notes_lexer = QsciLexerPython(self._notes_editor)
        self._notes_font = QFont(DEFAULT_FONT_FAMILY, 14)
        self._notes_font.setStyleHint(QFont.StyleHint.Monospace)
        self._notes_lexer.setFont(self._notes_font)
        self._configure_lexer_colors(self._notes_lexer)
        self._notes_editor.setLexer(self._notes_lexer)

        notes_tab_layout.addWidget(self._notes_editor)
        self.tabs.addTab(notes_tab, "📝 Beat Notes & Scratchpad (.txt)")

        # Tab 2: 📡 Activity & Status Log
        log_tab = QWidget()
        log_tab_layout = QVBoxLayout(log_tab)
        log_tab_layout.setContentsMargins(4, 4, 4, 4)
        log_tab_layout.setSpacing(4)

        log_top_bar = QHBoxLayout()
        log_label = QLabel("Real-Time Engine, Playback & Recording Activity Log:", log_tab)
        log_label.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 12px;")
        log_top_bar.addWidget(log_label)
        log_top_bar.addStretch()

        clear_log_btn = QPushButton("Clear Log", log_tab)
        clear_log_btn.setObjectName("toolBtn")
        clear_log_btn.clicked.connect(lambda: self.console.clear())
        log_top_bar.addWidget(clear_log_btn)
        log_tab_layout.addLayout(log_top_bar)

        self.console = QTextEdit(log_tab)
        self.console.setObjectName("console")
        self.console.setReadOnly(True)
        self.console.append("✓ <b>Vortex Studio v5 ready</b>. Live audio listening on PipeWire port 57120.")
        self.console.append("✓ Use the top editor for active live beats, and the spacious <b>Beat Notes</b> tab to store recipes, comments, and copy/paste patterns!")
        log_tab_layout.addWidget(self.console)

        self.tabs.addTab(log_tab, "📡 Activity & Status Log")
        bottom_layout.addWidget(self.tabs)

        self.splitter.addWidget(bottom_container)

        # Set balanced splitter proportions: 55% top, 45% bottom
        self.splitter.setSizes([500, 380])
        main_layout.addWidget(self.splitter)

        # Status Bar at bottom
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready | Vortex Studio by Jack Northrup & Esperanza AI Companion | SuperDirt @ 57120")

        # Recording timer
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update_recording_timer)

        # Playback poll timer
        self._play_timer = QTimer(self)
        self._play_timer.setInterval(500)
        self._play_timer.timeout.connect(self._check_playback_finished)

        # Global Keyboard Shortcuts
        QShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Return), self._editor).activated.connect(self.evaluate_block)
        QShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Enter), self._editor).activated.connect(self.evaluate_block)
        QShortcut(QKeySequence.StandardKey.Save, self).activated.connect(self.save_file)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self).activated.connect(self.save_file_as)
        QShortcut(QKeySequence.StandardKey.Open, self).activated.connect(self.load_file)
        QShortcut(QKeySequence("Shift+Escape"), self).activated.connect(self.hush_sound)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.toggle_recording)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self.toggle_line_numbers)

        self.show()

    def _configure_lexer_colors(self, lexer):
        lexer.setDefaultColor(QColor("#cdd6f4"))
        lexer.setDefaultPaper(QColor("#181825"))
        lexer.setColor(QColor("#6c7086"), QsciLexerPython.Comment)
        lexer.setColor(QColor("#6c7086"), QsciLexerPython.CommentBlock)
        lexer.setColor(QColor("#f9e2af"), QsciLexerPython.Number)
        lexer.setColor(QColor("#a6e3a1"), QsciLexerPython.DoubleQuotedString)
        lexer.setColor(QColor("#a6e3a1"), QsciLexerPython.SingleQuotedString)
        lexer.setColor(QColor("#cba6f7"), QsciLexerPython.Keyword)
        lexer.setColor(QColor("#89b4fa"), QsciLexerPython.FunctionMethodName)
        lexer.setColor(QColor("#fab387"), QsciLexerPython.Operator)

    def adjust_font_size(self, delta):
        self._font_size = max(10, min(36, self._font_size + delta))
        self._editor_font.setPointSize(self._font_size)
        self._lexer.setFont(self._editor_font)
        self._editor.setLexer(self._lexer)

        self._notes_font.setPointSize(max(10, self._font_size - 2))
        self._notes_lexer.setFont(self._notes_font)
        self._notes_editor.setLexer(self._notes_lexer)

        self.log(f"Font size adjusted: Editor={self._font_size}pt, Notes={max(10, self._font_size - 2)}pt")

    def toggle_line_numbers(self):
        """Toggle line numbers visibility in main editor and notes scratchpad."""
        self._show_line_numbers = not self._show_line_numbers
        if self._show_line_numbers:
            self._editor.setMarginWidth(0, "0000")
            self._notes_editor.setMarginWidth(0, "000")
            self.line_num_btn.setText("Remove Line #s")
            self.line_num_btn.setToolTip("Click to remove line numbers (Ctrl+L)")
            self.log("👁️ <b>Line numbers restored.</b>")
            self.status_bar.showMessage("Line numbers enabled", 2500)
        else:
            self._editor.setMarginWidth(0, 0)
            self._notes_editor.setMarginWidth(0, 0)
            self.line_num_btn.setText("Show Line #s")
            self.line_num_btn.setToolTip("Click to restore line numbers (Ctrl+L)")
            self.log("👁️ <b>Line numbers removed.</b> Clean distraction-free view.")
            self.status_bar.showMessage("Line numbers removed", 2500)

    def log(self, message, is_error=False):
        color = "#f38ba8" if is_error else "#a6e3a1"
        self.console.append(f"<span style='color: {color};'>{message}</span>")
        self.console.verticalScrollBar().setValue(
            self.console.verticalScrollBar().maximum()
        )
        if is_error:
            self.status_bar.showMessage(f"⚠️ Error: {message.replace('<b>','').replace('</b>','')[:80]}", 6000)

    # ==================== MAIN SCRIPT: SAVE / SAVE AS / LOAD / CLEAR ====================

    def save_file(self):
        """Quick-save to current file, or trigger Save As if untitled."""
        if not self._current_file:
            self.save_file_as()
            return

        try:
            with open(self._current_file, "w", encoding="utf-8") as f:
                f.write(self._editor.text())
            base_name = os.path.basename(self._current_file)
            self.setWindowTitle(f"🎵 Vortex Studio {__version__} — by Jack Northrup & Esperanza AI Companion [{base_name}]")
            self.file_badge.setText(f"📄 {base_name}")
            self.log(f"💾 <b>Quick-Saved script:</b> <code>{self._current_file}</code>")
            self.status_bar.showMessage(f"Saved: {base_name}", 4000)
        except Exception as e:
            self.log(f"⚠️ Error saving script: {e}", is_error=True)

    def save_file_as(self):
        """Prompt user for a custom filename and save."""
        default_path = self._current_file or os.path.join(SAVED_DIR, "my_custom_beat.py")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Vortex Beat Script As",
            default_path,
            "Python Files (*.py);;Text Files (*.txt);;All Files (*)",
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self._editor.text())
                self._current_file = file_path
                base_name = os.path.basename(file_path)
                self.setWindowTitle(f"🎵 Vortex Studio {__version__} — by Jack Northrup & Esperanza AI Companion [{base_name}]")
                self.file_badge.setText(f"📄 {base_name}")
                self.log(f"💾 <b>Saved script as:</b> <code>{file_path}</code>")
                self.status_bar.showMessage(f"Saved As: {base_name}", 4000)
            except Exception as e:
                self.log(f"⚠️ Error saving file as: {e}", is_error=True)

    def load_file(self):
        """Open an existing beat script to edit and run."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Vortex Beat Script",
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
                self.setWindowTitle(f"🎵 Vortex Studio {__version__} — by Jack Northrup & Esperanza AI Companion [{base_name}]")
                self.file_badge.setText(f"📄 {base_name}")
                self.log(f"📂 <b>Loaded script:</b> <code>{file_path}</code>")
                self.status_bar.showMessage(f"Loaded: {base_name}", 4000)
            except Exception as e:
                self.log(f"⚠️ Error loading file: {e}", is_error=True)

    def clear_screen(self):
        """Clear the main editor for a clean workspace."""
        if len(self._editor.text().strip()) > 50:
            reply = QMessageBox.question(
                self,
                "Clear Editor?",
                "Are you sure you want to clear the editor screen for a fresh canvas?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._editor.setText("")
        self._current_file = None
        self.setWindowTitle(f"🎵 Vortex Studio {__version__} — by Jack Northrup & Esperanza AI Companion [Untitled]")
        self.file_badge.setText("[Untitled Script]")
        self.log("🗑 <b>Editor cleared.</b> Blank canvas ready!")

    def load_preset(self, index):
        name = self.preset_combo.currentText()
        code = PRESETS.get(name)
        if code:
            self._editor.append("\n\n" + code)
            self.log(f"Added preset: <b>{name}</b>")
            self._editor.setCursorPosition(self._editor.lines(), 0)

    # ==================== BEAT NOTES & SCRATCHPAD CONTROLS ====================

    def save_notes(self):
        """Quick-save notes scratchpad to the current notes file."""
        if not self._notes_current_file:
            self.save_notes_as()
            return

        try:
            with open(self._notes_current_file, "w", encoding="utf-8") as f:
                f.write(self._notes_editor.text())
            base_name = os.path.basename(self._notes_current_file)
            self.notes_file_badge.setText(f"📄 {base_name}")
            self.log(f"💾 <b>Saved Beat Notes:</b> <code>{self._notes_current_file}</code>")
            self.status_bar.showMessage(f"Notes Saved: {base_name}", 4000)
        except Exception as e:
            self.log(f"⚠️ Error saving notes: {e}", is_error=True)

    def save_notes_as(self):
        """Save notes scratchpad to a new .txt file in beat_notes/."""
        default_path = self._notes_current_file or os.path.join(NOTES_DIR, "my_beat_recipes.txt")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Beat Notes As",
            default_path,
            "Text Files (*.txt);;Markdown Files (*.md);;Python Files (*.py);;All Files (*)",
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self._notes_editor.text())
                self._notes_current_file = file_path
                base_name = os.path.basename(file_path)
                self.notes_file_badge.setText(f"📄 {base_name}")
                self.log(f"💾 <b>Saved Notes As:</b> <code>{file_path}</code>")
                self.status_bar.showMessage(f"Notes Saved As: {base_name}", 4000)
            except Exception as e:
                self.log(f"⚠️ Error saving notes as: {e}", is_error=True)

    def load_notes_file(self):
        """Load any text file or beat collection into the notes scratchpad."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Beat Notes / Recipe File",
            NOTES_DIR,
            "Text Files (*.txt);;Markdown Files (*.md);;Python Files (*.py);;All Files (*)",
        )
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._notes_editor.setText(content)
                self._notes_current_file = file_path
                base_name = os.path.basename(file_path)
                self.notes_file_badge.setText(f"📄 {base_name}")
                self.log(f"📂 <b>Loaded Beat Notes:</b> <code>{file_path}</code>")
                self.status_bar.showMessage(f"Loaded Notes: {base_name}", 4000)
            except Exception as e:
                self.log(f"⚠️ Error loading notes file: {e}", is_error=True)

    def insert_selected_note_into_editor(self):
        """Insert selected text (or current line) from notes into main code editor at cursor."""
        snippet = ""
        if self._notes_editor.hasSelectedText():
            snippet = self._notes_editor.selectedText().strip()
        else:
            line_idx, _ = self._notes_editor.getCursorPosition()
            snippet = self._notes_editor.text(line_idx).strip()

        if not snippet:
            self.log("⚠️ No text selected in Beat Notes to insert.", is_error=True)
            return

        # If it's a raw pattern string (not valid python statement), wrap in a pattern stream
        if not snippet.startswith("p(") and not snippet.startswith("#") and not "=" in snippet and not snippet.startswith("hush()"):
            wrapped = f'p("custom", s("{snippet}")\n    >> room(0.3)\n)'
            self._editor.insert(f"\n{wrapped}\n")
            self.log(f"📋 Inserted pattern wrapped in player: <code>{snippet}</code>")
        else:
            self._editor.insert(f"\n{snippet}\n")
            self.log(f"📋 Inserted snippet into Main Editor: <code>{snippet[:50]}...</code>")

        self.status_bar.showMessage("Snippet copied to Main Editor", 3000)
        self._editor.setFocus()

    def run_selected_note(self):
        """Evaluate the selected note or line directly in the audio engine!"""
        snippet = ""
        if self._notes_editor.hasSelectedText():
            snippet = self._notes_editor.selectedText().strip()
        else:
            line_idx, _ = self._notes_editor.getCursorPosition()
            snippet = self._notes_editor.text(line_idx).strip()

        if not snippet or snippet.startswith("#"):
            self.log("⚠️ Highlight a beat recipe or code snippet in notes to run.", is_error=True)
            return

        # If it's a raw pattern string (e.g. "bd*4 [~ cp]*2"), wrap it automatically
        if not snippet.startswith("p(") and not "=" in snippet and not snippet.startswith("hush()"):
            exec_code = f'p("notes_audition", s("{snippet}") >> room(0.35))'
        else:
            exec_code = snippet

        self.log(f"▶ <b>Running from Notes:</b> <code>{exec_code[:60]}...</code>")
        try:
            exec(exec_code, vars(self._dsl_module))
            self.status_bar.showMessage("Auditioning recipe from notes...", 3000)
        except Exception as e:
            self.log(f"⚠️ <b>Note Execution Error:</b> {e}", is_error=True)

    def clear_notes(self):
        """Clear notes scratchpad with confirmation."""
        if len(self._notes_editor.text().strip()) > 50:
            reply = QMessageBox.question(
                self,
                "Clear Notes?",
                "Are you sure you want to clear the notes scratchpad?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._notes_editor.setText("")
        self._notes_current_file = None
        self.notes_file_badge.setText("[Untitled Notes]")
        self.log("🗑 Beat Notes scratchpad cleared.")

    # ==================== LIVE CODE EVALUATION ====================

    def hush_sound(self):
        try:
            hush_func = getattr(self._dsl_module, "hush", None)
            if hush_func:
                hush_func()
            self.log("🛑 <b>HUSH</b>: All live streams silenced.")
            self.status_bar.showMessage("All sound silenced (Hush)", 3000)
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

        first_line = code.split("\n")[0][:50]
        self.log(f"▶ <b>Running:</b> <code>{first_line}...</code>")

        try:
            exec(code, vars(self._dsl_module))
            self.status_bar.showMessage(f"Running: {first_line}...", 3000)
            if span:
                self.highlight_block(span[0], span[1])
        except Exception as e:
            self.log(f"⚠️ <b>Execution Error:</b> {e}", is_error=True)

    def highlight_block(self, start_line, end_line):
        pool = QThreadPool.globalInstance()
        runnable = HighlightLines(self._editor, (start_line, end_line))
        pool.start(runnable)

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
            self.status_bar.showMessage("🔴 RECORDING LIVE AUDIO OUTPUT TO MP3...")
            self.log(f"🔴 <b>RECORDING STARTED:</b> Capturing live audio to MP3...")
        except Exception as e:
            self.log(f"⚠️ Failed to start MP3 recording: {e}", is_error=True)

    def _update_recording_timer(self):
        if self._is_recording:
            elapsed = int(time.time() - self._record_start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            self.rec_btn.setText(f"⏹ Stop REC ({mins:02d}:{secs:02d})")
            self.status_bar.showMessage(f"🔴 Recording ({mins:02d}:{secs:02d}) -> {os.path.basename(self._temp_mp3_path)}")

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
            self.status_bar.showMessage(f"Saved MP3: {base_name} ({file_size_kb:.1f} KB)", 5000)

            # Prompt user if they want to Save As a custom filename
            reply = QMessageBox.question(
                self,
                "MP3 Recording Saved!",
                f"Your recording was captured as:\n\n{base_name}\n({file_size_kb:.1f} KB)\n\nWould you like to Save As a custom filename?",
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
            self.status_bar.showMessage(f"Loaded MP3: {base_name}", 4000)

    def toggle_play_mp3(self):
        if self._play_proc is not None:
            self.stop_play_mp3()
        else:
            self.start_play_mp3()

    def start_play_mp3(self):
        if not self._current_mp3_path or not os.path.exists(self._current_mp3_path):
            self.load_mp3()
            if not self._current_mp3_path:
                return

        try:
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
            self.status_bar.showMessage(f"Playing MP3: {base_name}")
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
        self.status_bar.showMessage("MP3 playback stopped.", 3000)

    def _check_playback_finished(self):
        if self._play_proc is not None:
            ret = self._play_proc.poll()
            if ret is not None:
                self.stop_play_mp3()

    def closeEvent(self, event):
        if self._is_recording:
            self.stop_recording()
        if self._play_proc is not None:
            self.stop_play_mp3()
        super().closeEvent(event)


def start_guiv6():
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
    start_guiv6()
