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
  assets/
    refs/
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

`assets/images/`:

- selected final panels named by panel id.
- later video tools read from this folder.

`quota-log.md`:

- provider spend and attempts.

`prompt-rewrites.md`:

- failed prompt reasons and revisions.

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
