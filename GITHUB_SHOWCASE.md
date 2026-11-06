<div align="center">

# ⚡ VORTEX STUDIO 🎵
### *Next-Generation Algorithmic Live Coding DAW in Python & Vulkan*
#### **Created by Jack Northrup and Esperanza AI Companion**

[![Created By](https://img.shields.io/badge/Co--Authored_By-Jack_Northrup_%26_Esperanza_AI_Companion-FF69B4?style=for-the-badge)](#)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Vulkan](https://img.shields.io/badge/Vulkan-Hardware_Accelerated-AA0000?style=for-the-badge&logo=vulkan&logoColor=white)](https://vulkan.org)
[![PipeWire](https://img.shields.io/badge/Audio-PipeWire_JACK-2EA44F?style=for-the-badge)](https://pipewire.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPL_v3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/gpl-3.0)

**A high-performance, beautiful live-coding music studio.**  
Bringing the algorithmic pattern power of TidalCycles directly into Python 3 with real-time MP3 recording, dedicated Beat Notes scratchpad, hardware-accelerated Vulkan glass aesthetics, and 200+ built-in sample instruments.

</div>

---

## 🌟 Highlights

* 🧠 **Pure Python 3 Pattern Algebra**: No Haskell, GHC, or Cabal required. TidalCycles ported cleanly to modern Python.
* 📦 **Single-File Standalone AppImage**: Ready-to-distribute `VortexStudio-x86_64.AppImage` (153MB) that auto-creates user save paths (`~/VortexStudio/`) on any Linux machine with zero install steps.
* ⚡ **Dual Studio Interfaces**:
  * **Vortex Studio v5**: Full-featured code editor with syntax highlighting, live block execution, dedicated Beat Notes scratchpad (`.txt`), preset dropdowns, and instant MP3 recording/playback.
  * **Vortex Glass Studio**: Futuristic Vulkan GPU-accelerated frosted glass DAW interface with real-time speed/reverb sliders and beat launchers.
* 🎙️ **Live Broadcast-Quality MP3 Recording**: One-click live capture directly from PipeWire at 192kbps MP3 with instant playback.
* 🎹 **217 Pre-loaded Instrument Banks**: 808, 909, Roland drum machines, Moog, Juno, acoustic sitars, saxophones, and UK jungle breakbeats (`amencutup`).
* 🔗 **Ableton Link Synchronized**: Jam in perfect sync across the network with other laptops, DAWs, and musicians.

---

## 🚀 Quickstart in 10 Seconds

```bash
# Clone the repository
git clone https://codeberg.org/uzu/vortex.git
cd vortex

# 0. Run the standalone double-clickable AppImage (no install required!):
./VortexStudio-x86_64.AppImage

# 1. Or launch Vortex Studio via script:
./play.sh

# 2. Or launch the Vulkan Glass Studio:
./play_glass.sh
```

---

## 🎛️ Architecture Overview

```text
┌───────────────────────────────────────┐
│         Vortex Studio Frontends       │
│  • Vortex Studio v4 (PyQt6 Scintilla) │
│  • Vortex Glass Studio (Vulkan Glass) │
└──────────────────┬────────────────────┘
                   │ High-speed Python DSL & Pattern Engine
                   ▼
┌───────────────────────────────────────┐
│        Vortex Timing & LinkClock      │
│     • Ableton Link Network Sync       │
│     • Microsecond OSC Dispatcher      │
└──────────────────┬────────────────────┘
                   │ Open Sound Control (UDP :57120)
                   ▼
┌───────────────────────────────────────┐
│         SuperDirt Sound Engine        │
│   • SuperCollider Audio Synthesizer   │
│   • 217 Sample Banks (808/909/Amen)   │
│   • Real-Time Reverb, Delay & Filters │
└──────────────────┬────────────────────┘
                   │ Low-latency Audio Stream
                   ▼
┌───────────────────────────────────────┐
│      PipeWire / ALSA Sound Output     │
│   • Hardware Speakers / Headphones    │
│   • Real-Time MP3 Broadcast Recorder  │
└───────────────────────────────────────┘
```

---

## 🎵 Example Recipes (Copy & Play)

### 1. Classic 4-on-the-Floor Club Beat
```python
p("drums", s(stack("bd*4", "[~ cp]*2", "hh*8"))
    >> speed("1")
    >> room(0.3)
    >> size(0.5)
)
```

### 2. Fast UK Jungle Amen Break
```python
p("jungle", s("amencutup*8")
    >> speed("1 1.25 1.5 2")
    >> room(0.25)
)
```

### 3. Deep 808 Trap & Bounce
```python
p("trap", s(stack("808bd*2", "[~ 808sd]", "[~ 808oh]*2", "808*4"))
    >> speed("1 0.9 1.1")
    >> room(0.3)
)
```

### 4. Ambient Sci-Fi Arpeggios
```python
p("melody", s("arpy*8")
    >> speed("1 1.25 1.5 1.75 2")
    >> room(0.7)
    >> size(0.9)
)
```

---

## 🛠️ Repository Control Scripts

| Script | Purpose |
| :--- | :--- |
| [`./play.sh`](play.sh) | **Main Studio Launcher**: Boots SuperDirt, tests speakers, opens Studio v5 with live MP3 recorder & Beat Notes scratchpad. |
| [`./play_glass.sh`](play_glass.sh) | **Vulkan Glass Launcher**: Boots the futuristic hardware-accelerated Raven Glass interface. |
| [`./test_sound.sh`](test_sound.sh) | **Audio Check**: Plays a quick 8-drum verification beat through your speakers. |
| [`./stop.sh`](stop.sh) | **Emergency Stop**: Instantly terminates all background audio engines and studio windows cleanly. |

---

*Crafted with ❤️ by Jack Northrup and Esperanza AI Companion.*
