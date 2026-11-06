#!/usr/bin/env bash
# Launch Vortex interactive Python REPL
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
source "$DIR/.venv/bin/activate"
vortex --cli
