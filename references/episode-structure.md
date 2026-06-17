# Episode Structure Spec

Status: M0 draft

This is the canonical V1 episode structure. It must stay compatible with existing video composer conventions.

```text
episodes/<episode-id>/
  episode-meta.json
  outline.md
  script.json
  storyboard.json
  prompts.json
  prompts-jimeng.json
  prompts-gpt-image.json
  style-profile.md
  character-cards.md
  visual-bible.md
  quota-log.md
  prompt-rewrites.md
  caption-layout.json       # optional: manual line breaks per panel
  selected-candidates.json  # approved raw source per panel
  assets/
    refs/
    candidates/
    images-raw/
    images/
    audio/
    video/
  output/
    publish/
    draft.mp4
    qc-report.md
```

## File Responsibilities

`episode-meta.json`:

- production mode.
- draft mode flag.
- target panel count.
- provider plan.
- quota budget.

Example:

```json
{
  "episode_id": "paper-bride-001",
  "production_mode": "pure_comic",
  "draft_mode": false,
  "target_panel_count": 8,
  "provider_plan": {
    "style_anchor": "gpt-image",
    "production_panels": "jimeng"
  },
  "jimeng_budget": {"max_prompts": 8, "candidates_per_panel": 1},
  "gpt_image_budget": {"max_images": 2},
  "minimax_budget": {"tts": false, "video": false}
}
```

`script.json`:

- canonical segment/panel text.
- must remain compatible with `comic-video-composer` for later video conversion.
- in pure comic mode, each segment `id` must equal the panel id, such as `"p001"`.
- segment `text` is the single source of truth for carousel caption text and future TTS narration.

`storyboard.json`:

- panel ids, story beats, visual descriptions, and draft caption notes.
- accepted caption text must be promoted into `script.json`.

`prompts.json`:

- shared prompt planning file with stable ids.
- do not pass mixed-provider `prompts.json` directly to a provider runner.
- use provider-specific files such as `prompts-jimeng.json` and `prompts-gpt-image.json` until runner-side provider filtering exists.

`visual-bible.md`:

- user-approved visual direction.
- summarizes style profile, character cards, references, world rules, text policy, and provider plan.

`assets/refs/`:

- style anchors and character references.

`assets/images-raw/`:

- provider outputs and manually imported candidates.

`assets/candidates/`:

- local candidate images produced during experiments or built-in image generation.
- may also be referenced by `selected-candidates.json`.
- keep large image files local; commit only text manifests and specs.

`assets/images/`:

- selected final panels named by panel id.
- later video tools read from this folder.

`quota-log.md`:

- provider spend and attempts.

`prompt-rewrites.md`:

- failed prompt reasons and revisions.

`caption-layout.json` (optional):

- Per-episode manual line-break config for caption cards.
- Each entry is either a list of lines or an object with `lines` and optional `source`.
- The joined text of each entry must equal the matching `script.json` segment text — the render script enforces this hard.
- Do not use this file to change caption wording — only to control how lines break visually.

`selected-candidates.json`:

- Manifest of approved raw image sources for each panel.
- Required when multiple raw candidates exist.
- The render and QC scripts use this instead of guessing the first `assets/images-raw/pNNN_*.png`.

Example:

```json
{
  "p001": "assets/images-raw/p001_002.png",
  "p002": "assets/images-raw/p002_001.png"
}
```

## Post-Production Scripts

These scripts live in `skills/story-video-factory/scripts/`. Run from the project root.

| Script | Purpose |
|--------|---------|
| `new_pure_comic_episode.py <episode> --title "..."` | Create a new pure-comic episode scaffold from the canonical template |
| `render_lettered_panels.py <episode>` | Batch-render captioned panels from raw assets into `assets/images/`; supports `--style douyin-msyh-top` |
| `build_publish_carousel.py <episode>` | Copy final images to numbered `output/publish/carousel/` folder; supports `--include-cover` |
| `generate_qc_report.py <episode>` | Generate QC report skeleton with auto-filled objective fields |
| `generate_publish_pack.py <episode>` | Generate publish pack draft (titles, cover text, hashtags) |
| `prepare_pure_comic_episode.py <episode>` | Orchestrate all four steps in order |

All scripts accept `--help`. The orchestrator accepts `--skip-render`, `--skip-carousel`, `--skip-qc`, `--skip-pack`, `--contact-sheet`, `--force`, `--caption-style`, `--include-cover`.

## Templates And Examples

Start new pure comic episodes from:

```bash
python skills/story-video-factory/scripts/new_pure_comic_episode.py episodes/<episode-id> --title "故事标题" --panel-count 11
```

The script copies `references/templates/pure-comic-episode/`, creates local asset/output folders, writes `episode-meta.json`, and initializes empty provider manifests.

Inspect the text-only M1 example at:

```text
references/examples/star-in-uniform-001/
```

Examples intentionally exclude media assets and publish outputs. Large files stay in local `episodes/<episode-id>/assets/` and `episodes/<episode-id>/output/`.

## Naming

Episode id:

```text
<series-or-topic>-<short-slug>-001
```

Panel ids:

```text
p001, p002, p003
```

The same panel id must be used across `script.json`, `storyboard.json`, prompt files, raw candidates, and selected final images.

Example `script.json` segment:

```json
{
  "segments": [
    {"id": "p001", "text": "民国十三年，苏州旧宅办了一场冥婚。"}
  ]
}
```

Raw candidates:

```text
assets/images-raw/p001_001.png
assets/images-raw/p001_002.png
```

Selected panel:

```text
assets/images/p001.png
```
