#!/usr/bin/env bash
# Launch script for Vortex AI DJ
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
source "$DIR/.venv/bin/activate"
python "$DIR/vortex_ai_dj.py" "$@"
