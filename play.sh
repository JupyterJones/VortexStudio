#!/usr/bin/env bash
# All-In-One Launcher for Vortex Studio v8
# Created by Jack Northrup & Esperanza AI Companion
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
export DISPLAY="${DISPLAY:-:0.0}"
export PYTHONWARNINGS="ignore"
export QT_LOGGING_RULES="qt.qpa.theme.gnome.warning=false"

# Trap Ctrl+C (SIGINT) and exit cleanly
cleanup() {
    echo ""
    echo "Shutting down Vortex Studio cleanly..."
    if [ -n "$SC_PID" ]; then
        kill "$SC_PID" 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "=============================================="
echo "      🎵 Starting Vortex Studio v8 🎵        "
echo "  by Jack Northrup & Esperanza AI Companion   "
echo "=============================================="

# 1. Check if SuperDirt is already running on port 57120
if ! ss -uln 'sport = :57120' | grep -q '57120'; then
    echo "[1/3] Booting SuperDirt audio engine in the background..."
    pw-jack sclang "$DIR/start_superdirt.scd" > /tmp/superdirt.log 2>&1 &
    SC_PID=$!

    # Wait up to 20 seconds for port 57120 to open
    echo -n "      Waiting for audio engine to initialize..."
    for i in {1..20}; do
        if ss -uln 'sport = :57120' | grep -q '57120'; then
            echo " Ready!"
            break
        fi
        sleep 1
        echo -n "."
    done
else
    echo "[1/3] SuperDirt audio engine is already active!"
fi

# 2. Play a test chime to verify speakers
echo "[2/3] Testing speaker output (chime)..."
"$DIR/.venv/bin/python" -c "
import pyliblo3 as liblo, time
try:
    a = liblo.Address(57120)
    liblo.send(a, '/dirt/play', 's', 'arpy', 'speed', 1.0, 'room', 0.5)
    time.sleep(0.2)
    liblo.send(a, '/dirt/play', 's', 'arpy', 'speed', 1.5, 'room', 0.5)
except:
    pass
" 2>/dev/null

# 3. Launch the Vortex Studio GUI v5
echo "[3/3] Opening Vortex Studio v5..."
echo "----------------------------------------------"
echo "  • [▶ Run] (Ctrl+Enter) to evaluate code block"
echo "  • [🛑 Stop] (Shift+Esc) to hush live patterns"
echo "  • [💾 Save] & [💾 Save As] for scripts"
echo "  • [📂 Load Script] to load any .py beat file"
echo "  • [⏺ Record MP3] to capture live to MP3"
echo "  • [▶ Play MP3] & [📂 Load MP3] for playback"
echo "  • [📝 Beat Notes] tab to store recipes & comments"
echo "  • [A-] / [A+] & [Remove Line #s] to customize view"
echo "----------------------------------------------"

source "$DIR/.venv/bin/activate"
python -m vortex.guiv8

cleanup
