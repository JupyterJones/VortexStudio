# ==========================================================
# 🎵 Vortex Studio — Welcome Script
# Created by Jack Northrup & Esperanza AI Companion
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
