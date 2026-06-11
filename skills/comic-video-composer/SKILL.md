---
name: comic-video-composer
description: Compose comic images + TTS audio into a finished 9:16 short video with subtitles, Ken Burns camera motion, and quality checks, using FFmpeg. Use whenever the user wants to turn images into a video, add subtitles or narration audio to images, align TTS audio with panels, merge clips, burn subtitles, or quality-check a draft video. Trigger on phrases like 合成视频, 图转视频, 加字幕, 配音对齐, compose, render draft.
---

# Comic Video Composer

## Role

Turn approved assets (panel images + per-segment TTS audio + script JSON) into `output/draft.mp4`. Everything runs locally with FFmpeg; no generation quota is spent here.

## Required Inputs

Refuse to compose (and say what is missing) unless these exist:

- `script.json` — segments with `id` and `text` (see `chuke-storytelling-video` format).
- `assets/images/` — one image per segment, named `<segment-id>.png/jpg` (a panel may be reused by listing it for several ids in a mapping file).
- `assets/audio/` — one audio file per segment, named `<segment-id>.mp3/wav`.

## Pipeline

1. **Probe durations.** Get each audio file's duration with `ffprobe`. Segment display time = audio duration + 0.3s padding.
2. **Build subtitle file.** Generate an `.ass` subtitle from script text and probed durations using `scripts/make_subtitles.py`. One segment = one subtitle event. Wrap lines at ~14 CJK characters; max 2 lines.
3. **Render per-segment clips.** Use `scripts/compose.py`, which for each segment: scales/crops the image to 1080x1920, applies a slow zoom or pan (alternate direction per segment), muxes the segment audio.
4. **Concat + burn subtitles + music.** Concatenate clips, burn the `.ass` subtitles, optionally duck background music at -18dB under narration, output `output/draft.mp4` (H.264, yuv420p, 30fps, AAC).
5. **Quality check.** Run the checklist below; write `output/qc-report.md`.

Run the bundled scripts rather than rewriting this logic; only deviate when a step fails and needs a workaround.

## Quality Checklist

- Duration of video == sum of segment durations (±1s).
- No segment whose image is missing (script id without image → hard fail).
- Subtitles appear within 0.2s of their audio.
- First 3 seconds contain the hook segment, not a title card alone.
- Output is 1080x1920, 9:16, audio not clipping (check `ffmpeg -af volumedetect`).
- Spot-check 3 random timestamps with extracted frames (`ffmpeg -ss ... -vframes 1`) and view them.

## Camera Motion Defaults

- Zoom range 1.0 → 1.08 over the segment (subtle; comic art distorts if stronger).
- Alternate: zoom-in, zoom-out, pan-left, pan-right, in beat order.
- Hook/reveal segments may use a faster zoom (1.0 → 1.15).

## Scripts

- `scripts/compose.py` — full pipeline: probe, per-segment clips, concat, subtitles, music. Run `python scripts/compose.py --episode <dir>`; see `--help`.
- `scripts/make_subtitles.py` — standalone .ass generator if only subtitles need regenerating.

Both need `ffmpeg`/`ffprobe` on PATH. No other dependencies (pure stdlib).

## References

- `references/composition-spec.md`: encoding parameters, .ass style block, music ducking filtergraph.
