# 🎵 05 - Multi-Track Jam (Drums + Funky Bass)
# Run with [▶ Run Block] or [Ctrl] + [Enter]

# Channel 1: Driving drums
p("drums", s(stack("clubkick*4", "[~ realclaps]*2", "hh*8"))
    >> room(0.2)
)

# Channel 2: Funky Bassline
p("bass", s("bass1*4")
    >> speed("0.5 0.75 1 0.5")
    >> room(0.4)
)
