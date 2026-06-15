# Comic-To-Video Mode

Status: later phase

Comic-to-video mode starts from an approved pure comic episode. It should not bypass the pure comic review gates.

## Entry Requirements

- `script.json` approved.
- `assets/images/p*.png` approved.
- `output/qc-report.md` reviewed.
- User explicitly chooses to convert the carousel into video.

## Planned Flow

1. Reuse `script.json` as narration/subtitle source.
2. Reuse `assets/images/` as visual source.
3. Generate TTS with MiniMax or another provider.
4. Compose motion, subtitles, and audio with `comic-video-composer`.
5. Generate `output/draft.mp4`.
6. Review video before publishing.

## Current Rule

Do not start here. Produce or approve the pure comic package first.
