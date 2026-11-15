#!/usr/bin/env bash
# Technical QC of the final render -> reports/qc_report.txt
set -uo pipefail; cd "$(dirname "$0")/.."
F=${1:-final/street_talk_cinematic_1080x1920.mp4}; R=reports/qc_$(basename "$F" .mp4).txt; mkdir -p reports analysis/qc_frames
{
echo "== QC $(date -u +%FT%TZ) :: $F"
echo "-- container/streams"; ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,color_space,color_transfer,color_range,sample_rate,channels -of default=nw=1 "$F"
echo "-- source vs output duration"; for x in input/IMG_0611.mp4 "$F"; do ffprobe -v error -show_entries format=duration -of csv=p=0 "$x"; done
echo "-- A/V stream start/duration"; ffprobe -v error -show_entries stream=codec_type,start_time,duration -of csv=p=0 "$F"
echo "-- decode errors"; ffmpeg -v error -i "$F" -f null - 2>&1 | head -5; echo "(end)"
echo "-- black / freeze detection (black at fade-out end is expected)"; ffmpeg -hide_banner -nostats -i "$F" -an -vf "blackdetect=d=0.1:pix_th=0.06,freezedetect=n=0.003:d=2" -f null - 2>&1 | grep -E "black_|freeze_"; echo "(end)"
echo "-- loudness / true peak"; ffmpeg -hide_banner -nostats -i "$F" -vn -af ebur128=peak=true -f null - 2>&1 | sed -n '/Summary/,$p'
echo "-- clipping stats"; ffmpeg -hide_banner -nostats -i "$F" -vn -af astats=metadata=0 -f null - 2>&1 | grep -E "Overall|Peak level dB|Number of samples|Peak count" | head -6
} > $R 2>&1
for t in 1 3 8 30 70 120 165 168.5; do ffmpeg -hide_banner -v error -y -ss $t -i "$F" -frames:v 1 -vf scale=360:-2 analysis/qc_frames/out_$t.png; done
montage analysis/qc_frames/out_{1,3,8,30,70,120,165,168.5}.png -tile 8x1 -geometry +3+3 analysis/qc_frames/qc_sheet.png
cat $R
