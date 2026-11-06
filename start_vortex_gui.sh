#!/usr/bin/env bash
# Launch Vortex GUI Studio v8 (Live Coding + Beat Notes + Live MP3 Suite + Welcome Script + Auto-Create Save Paths)
# Created by Jack Northrup & Esperanza AI Companion
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
export DISPLAY="${DISPLAY:-:0.0}"
export PYTHONWARNINGS="ignore"
export QT_LOGGING_RULES="qt.qpa.theme.gnome.warning=false"
source "$DIR/.venv/bin/activate"
python -m vortex.guiv8
