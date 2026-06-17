# Pure Comic Mode

Status: primary V1 production mode

Pure comic mode is the current mainline for Story Video Factory. It produces a Douyin-ready image carousel first, then leaves video conversion as a later optional step.

## When To Use

Use `pure_comic` when the goal is a stable, reviewable, image-first story package:

- Douyin image carousel.
- No TTS or video required.
- Human review before image generation and before publishing.
- Provider quota should be spent on still-image quality first.

## Review Gates

Hard gates:

1. Story idea and outline approved.
2. `script.json` and `storyboard.json` approved.
3. `visual-bible.md` approved before spending provider quota.
4. Final selected images approved before publish pack.

Soft gates:

- Provider-specific prompt wording.
- QC report generation.
- Publish pack draft generation.

## Canonical Flow

1. Create episode folder with:

```bash
python skills/story-video-factory/scripts/new_pure_comic_episode.py episodes/<episode-id> --title "故事标题" --panel-count 11
```

2. Fill `episode-meta.json`, `outline.md`, `script.json`, and `storyboard.json`.
3. Draft `style-profile.md`, `character-cards.md`, and `visual-bible.md`.
4. Generate or import images into `assets/images-raw/`.
5. Record approved raw source paths in `selected-candidates.json`.
6. Run:

```bash
python skills/story-video-factory/scripts/prepare_pure_comic_episode.py episodes/<episode-id> --force --contact-sheet
```

For Douyin image posts where bottom UI would cover captions, prefer the top safe-zone Microsoft YaHei style:

```bash
python skills/story-video-factory/scripts/prepare_pure_comic_episode.py episodes/<episode-id> --caption-style douyin-msyh-top --include-cover --force --force-render --contact-sheet
```

7. Review `output/qc-report.md` and `output/publish/pack.md`.
8. Upload numbered images from `output/publish/carousel/`.

## Source Of Truth

- Caption text: `script.json` only.
- Manual line breaks: `caption-layout.json` only.
- Approved raw image source: `selected-candidates.json`.
- Final upload order: `script.json` segment order.
- Caption style preset: `references/caption-styles/douyin-msyh-top.json` for upper/left captions that avoid Douyin bottom UI.

## Non-Goals In V1

- No direct video generation.
- No TTS.
- No automatic Douyin upload.
- No strong automated character consistency.
- No provider-specific reference-image workflow unless separately implemented.
