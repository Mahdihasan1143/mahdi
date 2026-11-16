#!/usr/bin/env bash
# Clean version: raw footage only (continuous), Natural DSLR grade, subtitles + title + place list + punchline pops, bottom gradient for legibility.
set -euo pipefail; cd "$(dirname "$0")/.."
OUT=${1:-final/street_talk_v5_clean_1080x1920.mp4}
node scripts/07_subtitle_pngs.js > renders/sub_png.log
node scripts/09_list_graphics.mjs > renders/list.log
node scripts/17_pops.mjs > renders/pops.log
python3 scripts/18_plan_clean.py > renders/plan_clean.log
export PLAN=analysis/plan_clean.json BLK=blocks_clean TAG=v5
python3 scripts/14_blocks.py > renders/blocks_clean.log
SFX=analysis/sfx_clean.json python3 scripts/15_audio.py > renders/audio_v5.log
POP_Y=1150 GRAD=1 PRESET=${PRESET:-fast} python3 scripts/16_final.py "$OUT" > renders/final_v5.log 2>&1
echo DONE "$OUT"
