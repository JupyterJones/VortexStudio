#!/usr/bin/env bash
# Quick speaker & audio test
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
"$DIR/.venv/bin/python" -c "
import pyliblo3 as liblo
import time

addr = liblo.Address(57120)
print('Testing audio output through SuperDirt...')
beat = [
    ('808bd', 1.0, 0.4),
    ('hh', 1.0, 0.2),
    ('cp', 1.0, 0.3),
    ('hh', 1.0, 0.2),
    ('808bd', 1.0, 0.2),
    ('808bd', 1.2, 0.2),
    ('cp', 1.0, 0.3),
    ('arpy', 1.5, 0.5)
]

for sample, spd, pause in beat:
    print(f'  Playing: {sample}')
    liblo.send(addr, '/dirt/play', 's', sample, 'speed', spd, 'room', 0.4)
    time.sleep(pause)

print('Sound test complete!')
"
