# Composition Spec

## Encoding

- Container: MP4, H.264 (`libx264`), `yuv420p`, CRF 19, preset medium.
- Audio: AAC 192k, 44.1kHz stereo.
- 1080x1920, 30fps (25fps acceptable).

Douyin re-encodes uploads; CRF 19 keeps enough headroom that the platform re-encode does not visibly degrade line art.

## Subtitle Style (.ass)

Defined in `scripts/make_subtitles.py` header. Key choices:

- Font: Noto Sans CJK SC (fallback: 思源黑体 / 微软雅黑 — edit the Style line if the render machine lacks Noto).
- Size 72 at PlayResY 1920 (~3.7% of height), bold, white fill, 4px black outline, semi-transparent shadow box.
- MarginV 260: keeps text above Douyin's caption/progress UI zone.
- Max 2 lines, ~14 CJK chars/line. Longer → rewrite the script segment, don't shrink the font.

## Music Ducking

`compose.py --music` uses a fixed -18dB bed mixed under narration. For real sidechain ducking instead:

```text
[1:a]volume=0dB[bg];[0:a]asplit=2[nar][sc];
[bg][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];
[nar][duck]amix=inputs=2:duration=first[a]
```

## 16:9 → 9:16 Conversion (for landscape AI-video clips)

Minimax T2V outputs landscape only. Two recipes to fit a 16:9 clip into the 1080x1920 frame:

Center crop (loses sides — only when subject is centered):

```text
-vf "crop=ih*9/16:ih,scale=1080:1920"
```

Blur-pad (keeps full frame, cinematic letterbox feel):

```text
-filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"
```

Prefer requesting vertical clips at the source (image-to-video with 9:16 first frame) — conversion is the fallback.

## Common Failures

- **zoompan jitter**: caused by zooming a small source; the script pre-scales 2x to avoid it. If still visible, pre-scale 3x.
- **Subtitle path on Windows**: the `subtitles=` filter needs the drive colon escaped (`D\:/...`). The script handles this.
- **Audio drift over many segments**: always concat re-encoded uniform clips (same codec params), never mixed sources with `-c copy`.
- **CJK shown as boxes**: render machine missing the font; install Noto Sans CJK or change the Style line.
