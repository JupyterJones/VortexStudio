#!/usr/bin/env bash
# Kill all running Vortex and SuperCollider processes
echo "Stopping Vortex Studio and audio engine..."
pkill -9 -f "vortex" 2>/dev/null || true
pkill -9 -f "sclang" 2>/dev/null || true
pkill -9 -f "scsynth" 2>/dev/null || true
echo "All audio and Vortex processes stopped."
