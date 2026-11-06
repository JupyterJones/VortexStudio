# 🎵 Vortex & TidalCycles: Complete Beginner's Guide

Welcome Jack! This guide will take you from zero to live-coding music with **Vortex** and **SuperDirt**.

---

## 🧠 1. The Architecture (How It Works)

Making music with Vortex uses a two-part setup:

```
┌─────────────────────────────────┐               ┌──────────────────────────────────────┐
│       Vortex (The Brain)        │      OSC      │      SuperDirt (The Voice)           │
│   Python GUI / REPL Editor      │ ────────────> │  SuperCollider Audio Engine          │
│ • Calculates rhythms & timings  │  (Port 57120) │ • Plays samples (808, 909, breaks)   │
│ • Pure Python 3 (No Haskell!)   │               │ • Synthesizes tones & applies reverb │
└─────────────────────────────────┘               └──────────────────────────────────────┘
```

* **Vortex** is an algorithmic pattern generator written in **pure Python 3**. You type code, and it generates musical timings, polyrhythms, and triggers.
* **SuperDirt** is the audio engine (running inside **SuperCollider**). It receives network messages from Vortex and turns them into real sound through your speakers via **PipeWire**.
* **No Haskell needed!** Traditional TidalCycles requires Haskell/GHC, but Vortex ports the entire pattern algebra to Python.

---

## 🚀 2. Quick Start (2 Steps)

### Step 1: Start the Audio Engine (SuperDirt)
Open a terminal in `/home/jack/Desktop/vortex` and run:
```bash
./start_audio_server.sh
```
Wait a few seconds until you see:
```text
============================================================
  * SUPERDIRT IS READY & LISTENING ON PORT 57120 *          
  You can now start Vortex and make music!                  
  (Keep this terminal open while live coding)               
============================================================
```
> **Keep this terminal open!** It must stay running in the background while you make music.

---

### Step 2: Launch the Vortex Editor
Open a **second terminal** and launch the GUI code editor:
```bash
./start_vortex_gui.sh
```
*(Or if you prefer an interactive terminal REPL instead of the GUI, run `./start_vortex_cli.sh`)*

A GUI window will appear. You are now ready to make music!

---

## 🎹 3. How to Live Code in the Editor

1. **Write or click on a code block** in the editor.
2. Press <kbd>Ctrl</kbd> + <kbd>Enter</kbd> (or <kbd>Cmd</kbd> + <kbd>Enter</kbd>) to evaluate that block.
3. The pattern will start looping in perfect musical time!
4. You can edit the code *while it plays* and press <kbd>Ctrl</kbd> + <kbd>Enter</kbd> again to seamlessly transform the music on the next cycle.

### 🛑 The Panic Button (Stop All Sound)
Whenever you want to silence everything immediately, evaluate:
```python
hush()
```

---

## 🥁 4. Mini-Notation Rhythm Cheat Sheet

Vortex uses Tidal's famous **mini-notation** inside `s("...")` strings to define rhythms:

| Notation | Meaning | Example |
| :--- | :--- | :--- |
| `"bd"` | Play sample once in a cycle | `s("bd")` |
| `"bd sd"` | Divide the cycle evenly (Kick then Snare) | `s("bd sd")` |
| `"bd*4"` | Play 4 times evenly per cycle | `s("bd*4")` |
| `"~"` | Silence / Rest | `s("[~ cp]")` (clap on upbeat) |
| `[a b]` | Subdivide time into sub-steps | `s("[bd bd] [sn [hh hh]]")` |
| `a, b` | **Layer sounds simultaneously (Polyrhythm!)** | `s("bd*4, [~ cp]*2, hh*8")` |
| `/2` | Slow sound down across multiple cycles | `s("bass/2")` |

---

## 🔥 5. Ready-to-Play Musical Patterns

Copy and paste these blocks directly into your Vortex editor and hit <kbd>Ctrl</kbd> + <kbd>Enter</kbd>:

### 1. Classic 4-on-the-Floor Club Beat
```python
p("drums", s("bd*4, [~ cp]*2, hh*8")
    >> speed("1")
    >> room(0.3)
    >> size(0.5)
)
```

### 2. Fast Jungle / Drum & Bass Amen Break
```python
p("jungle", s("amencutup*8")
    .speed("1 1.25 1.5 2")
    >> room(0.2)
)
```

### 3. Deep 808 Electro Rhythm
```python
p("electro", s("808bd*2, [~ 808sd], 808hc*4, [~ 808oh]*2")
    >> speed("1 0.8 1.2")
    >> room(0.4)
)
```

### 4. Ambient Melodic Arpeggio
```python
p("melody", s("arpy*8")
    .speed("1 1.25 1.5 1.75 2")
    >> room(0.7)
    >> size(0.9)
)
```

### 5. Multi-Track Jam (Playing Drums + Bass Together)
You can run multiple independent named streams at the same time (`"drums"`, `"bass"`, `"lead"`):
```python
# Channel 1: Driving drums
p("drums", s("clubkick*4, [~ realclaps]*2, [hh*2]*4")
    >> room(0.2)
)

# Channel 2: Funky Bassline
p("bass", s("bass1*4")
    .speed("0.5 0.75 1 0.5")
    >> room(0.4)
)
```

---

## 🎛️ 6. Audio Effects & Sound Design

You can chain audio effects onto any sound using either the `>>` operator or method chaining `.effect(...)`:

* **`>> speed("1 2 0.5")`** : Changes playback speed and pitch (higher = faster & higher pitch, negative = backwards!).
* **`>> room(0.6)`** : Reverb amount (0 to 1).
* **`>> size(0.8)`** : Reverb room size (huge ambient space).
* **`>> pan("0 1 0.5")`** : Stereo panning (0 = left ear, 1 = right ear, 0.5 = center).
* **`>> lpf(800)`** : Low-pass filter (muffles higher frequencies for that underwater club feel).
* **`>> hpf(1200)`** : High-pass filter (cuts out low bass rumble).
* **`>> crush(4)`** : Bitcrusher (grungy 8-bit digital distortion, 16 down to 2).

---

## 📦 7. Installed Sound Sample Banks (217 Banks Ready!)

Over **200 instrument banks** are pre-loaded in your SuperDirt folder (`~/.local/share/SuperCollider/downloaded-quarks/Dirt-Samples/`). Here are some favorites:

* **Drum Machines**: `808`, `808bd`, `808sd`, `808cy`, `808hc`, `808oh`, `909`, `dr55`, `drumtraks`
* **Kicks & Snares**: `bd`, `clubkick`, `reverbkick`, `sn`, `sd`, `cp`, `realclaps`
* **Hi-Hats & Percussion**: `hh`, `hc`, `cb`, `tok`, `clak`, `tabla`, `tabla2`, `coins`
* **Breakbeats & Jungle**: `amencutup`, `breaks125`, `breaks152`, `breaks165`, `jungle`
* **Bass**: `bass`, `bass0`, `bass1`, `bass2`, `bass3`, `jungbass`, `jvbass`, `moog`
* **Synths & Melodic**: `arpy`, `juno`, `casio`, `pluck`, `sax`, `sitar`, `piano`
* **Glitch & Retro Sci-Fi**: `glitch`, `glitch2`, `invaders`, `industrial`, `bleep`, `sid`, `toys`

> **Tip**: You can select specific variations within a bank using numbers: e.g. `s("bd:0 bd:3 bd:5")` or `s("arpy:2 arpy:5")`.

---

## 🛠️ 8. Quick Troubleshooting

| Issue | Cause & Fix |
| :--- | :--- |
| **No sound when evaluating** | Make sure `./start_audio_server.sh` is running in another terminal. Look for *"SUPERDIRT IS READY"* in its output. |
| **Sound won't stop** | Evaluate `hush()` with <kbd>Ctrl</kbd> + <kbd>Enter</kbd>. |
| **Sound is too loud / quiet** | Adjust your normal desktop volume or PipeWire volume in system settings. |
| **GUI won't open** | Run `./start_vortex_gui.sh` or check that your X11 / Wayland display is active. |

---

*Created with ❤️ by Esperanza for Jack.*
