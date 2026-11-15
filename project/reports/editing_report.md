# Editing report — IMG_0611 → street_talk_cinematic_1080x1920.mp4

## Source (verified with ffprobe)
1080x1920 portrait (stored 1920x1080 + -90° rotation), HEVC Main10, **HDR HLG / BT.2020**, ~59.94 fps, 170.03 s, AAC 48k stereo.
(The brief assumed 512x910 / 30 fps — the real file is full 1080x1920 at 60 fps, so nothing is upscaled.)
SHA-256 of original: analysis/source.sha256. Original untouched (read-only).

## What was actually applied (verified in rendered frames / QC)
- HDR HLG -> SDR Rec.709 tone-map (zscale + Hable), then grade: gentle S-curve, warm highlights, slightly cool shadows, sat +7%.
- Light denoise (hqdn3d), mild sharpening, subtle vignette, very light temporal grain.
- 9 "virtual cut" segments timed to detected camera-swing moments; alternating wide / 1.12x punch-in, each with a slow 5% push-in.
- Title ("STREET TALK") + animated line + subtitle, and outro text, rendered from HTML/CSS in Chromium (transparent PNG), composited with FFmpeg. Fade to black at end.
- Audio: high-pass, light FFT denoise, EQ, compression, 2-pass loudnorm to -14 LUFS / -1.5 dBTP (source peaked at -0.4 dBFS), fades.
- Sound design synthesized with FFmpeg (no third-party assets): title impact, whoosh, outro drone — kept low under dialogue.

## Deliberately NOT done
- No dialogue/content cuts: one continuous take, no silences, and no transcript to cut safely.
- No subtitles (no transcript; no Whisper). Provide a transcript to add them.
- No name lower thirds (speaker names unknown). No stabilization (it would fight the intentional camera swings), no speed ramps, no light leaks, no music (none provided).
- No Adobe cloud tools used; nothing uploaded.

## Export
MP4 H.264 High@4.2, CRF 19 (maxrate 14M), yuv420p BT.709 tv, 1080x1920, 59.94 fps, AAC 256k 48 kHz, faststart.

## QC (reports/qc_report.txt)
No decode errors; A/V durations match (170.034/170.033 s, start 0); integrated -14.1 LUFS, true peak -1.4 dBFS, no clipping;
only black = intended 1.5 s fade-out at end; no frozen frames.

## Editable placeholders
Title/outro text: graphics/config.json (placeholders, not facts) -> run scripts/02_graphics.sh then scripts/04_render.py.
Pipeline: scripts/03_audio.sh, 04_render.py, 05_qc.sh.
