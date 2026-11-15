#!/usr/bin/env bash
# HDR(HLG, BT.2020) -> SDR BT.709, 30 fps, light denoise. Near-lossless intermediate so later renders skip the slow tone-map.
set -euo pipefail; cd "$(dirname "$0")/.."
ffmpeg -hide_banner -y -i input/IMG_0611.mp4 -an -map 0:v:0 \
 -vf "fps=30,zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,hqdn3d=1.2:1.2:2.5:2.5" \
 -c:v libx264 -preset veryfast -crf 11 -g 30 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 mezz/sdr30.mp4
