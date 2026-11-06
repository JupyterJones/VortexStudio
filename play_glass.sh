#!/usr/bin/env bash
# ⚡ Launch Vortex Raven Glass Studio (Vulkan Powered)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
export DISPLAY="${DISPLAY:-:0.0}"
export PYTHONWARNINGS="ignore"
export PYTHONPATH="$DIR"

# Cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down Vortex Glass Studio..."
    if [ -n "$SC_PID" ]; then
        kill "$SC_PID" 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "=============================================="
echo "   ⚡ Starting Vortex Glass Studio (Vulkan) ⚡ "
echo "=============================================="

# 1. Check if SuperDirt is running on port 57120
if ! ss -uln 'sport = :57120' | grep -q '57120'; then
    echo "[1/2] Booting SuperDirt audio engine..."
    pw-jack sclang "$DIR/start_superdirt.scd" > /tmp/superdirt.log 2>&1 &
    SC_PID=$!
    for i in {1..20}; do
        if ss -uln 'sport = :57120' | grep -q '57120'; then
            break
        fi
        sleep 1
    done
fi

echo "[2/2] Opening Vulkan Glass Interface..."
source "$DIR/.venv/bin/activate"
python -m vortex.raven_studio

cleanup
