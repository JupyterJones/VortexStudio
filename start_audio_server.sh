#!/usr/bin/env bash
# Launch SuperDirt audio engine with PipeWire-JACK
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
echo "Starting SuperDirt audio engine via PipeWire..."
pw-jack sclang "$DIR/start_superdirt.scd"
