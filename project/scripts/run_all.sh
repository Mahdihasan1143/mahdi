#!/usr/bin/env bash
# Full v3 pipeline from existing analysis: plan -> blocks -> audio -> subtitles -> final. Usage: run_all.sh [out.mp4]
set -euo pipefail; cd "$(dirname "$0")/.."
OUT=${1:-final/street_talk_v3_1080x1920.mp4}
.venv/bin/python scripts/13_plan.py > renders/plan.log
python3 scripts/14_blocks.py > renders/blocks.log
python3 scripts/15_audio.py > renders/audio.log
PRESET=${PRESET:-fast} python3 scripts/16_final.py "$OUT" > renders/final.log 2>&1
echo DONE "$OUT"
