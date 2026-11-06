# 🎵 01 - Acid House & Cyber Claps
# Run with [▶ Run Block] or [Ctrl] + [Enter]

p("drums", s(stack("gabba*4", "[~ cp]*2", "hh*8").every(3, fast(2)))
    >> speed("1 1.25")
    >> room(0.35)
    >> size(0.6)
)
