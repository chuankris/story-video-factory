---
name: story-video-factory
description: Orchestrate reviewed story-to-video production for Douyin and similar short-video platforms. Use when the user wants to plan a content factory, turn stories into comics or videos, choose between image/video/TTS providers, manage outline/script/storyboard/prompt/asset/composition states, or coordinate sub-skills. Always use this skill first when the user mentions making a story video, comic video, episode production, or asks "what's next" in a video production pipeline; it decides which sub-skill handles each step.
---

# Story Video Factory (Director)

## Role

Act as the production director for story-based short videos and comic carousels.

This skill coordinates the workflow. It does not replace specialized provider skills. Use it to decide what should happen next, which provider or sub-skill should be used, and what artifact should be produced for review.

## Current Mainline

The current V1 mainline is `pure_comic`: a reviewed Douyin image carousel with locally rendered captions.

Start here unless the user explicitly chooses video:

1. Load `references/modes/pure-comic.md`.
2. Create or inspect an episode folder using `references/templates/pure-comic-episode/`.
3. Move through outline, script, storyboard, visual bible, prompts, selected images, QC, and publish pack.

`comic_to_video` and `direct_video` are later-phase modes. Do not spend TTS or video quota until the user explicitly switches modes.

## Core Workflow

Always preserve the review-first order:

1. Select topic or story source.
2. Produce story outline for review.
3. Produce narration/caption script for review.
4. Produce storyboard for review.
5. Produce asset prompts and provider plan.
6. Generate or collect assets.
7. For `pure_comic`, package final images into a carousel; for video modes, produce TTS and compose draft video.
8. Quality-check draft output.
9. Prepare publishing pack.

Do not skip from script ideas to provider generation unless the user explicitly asks for a rough experiment.

## Production Modes

Choose one mode before routing providers:

- `pure_comic`: static comic panel carousel, post-rendered captions, no audio or video.
- `comic_to_video`: approved pure comic images plus narration, subtitles, and camera motion.
- `direct_video`: generated video clips assembled into a short video.
- `hybrid`: comic images for most beats, generated video for hook/reveal shots.

Prefer `pure_comic` for stable daily production. Use `hybrid` only when limited video-generation quota should be saved for important shots.

## Sub-Skill Routing

Route each step to its specialized skill:

| Step | Skill |
| --- | --- |
| Chuke storytelling / narration / episode review | `chuke-storytelling-video` |
| Comic panels via Jimeng browser automation | `jimeng-browser-provider` |
| Key frames / style refs via GPT-image | `gpt-image-provider` |
| Narration TTS and generated video clips | `minimax-media-provider` |
| Image-to-video composition, subtitles, QC | `comic-video-composer` |
| Title, cover, caption, tags, release checklist | `douyin-publisher-pack` |

If a sub-skill is not available in the current environment, continue with the matching reference in this skill and keep the artifact reviewable.

## References

Load only what is needed:

- `references/modes/pure-comic.md`: current default mode and reviewed carousel flow.
- `references/modes/comic-to-video.md`: later conversion mode after comic approval.
- `references/modes/direct-video.md`: later video-provider mode.
- `references/templates/pure-comic-episode/`: starting template for new pure comic episodes.
- `references/examples/star-in-uniform-001/`: text-only M1 example, no media assets.
- `references/workflow.md`: production states and review gates.
- `references/provider-routing.md`: choose GPT-image, Minimax, Jimeng, or local composition.
- `references/output-spec.md`: expected outputs for Douyin-oriented delivery.
- `references/skill-map.md`: big-skill/small-skill architecture.

## Operating Principles

- Keep humans in the loop for creative approvals and manual provider tasks.
- Treat browser automation as an efficiency aid, not a way to bypass platform rules.
- Save review artifacts with version suffixes before replacing accepted files.
- Separate style, provider, and composition concerns so the factory can support many story IPs.
- When waiting on rendering or asset generation, move another episode forward only through review-safe steps.

## Post-Production (Pure Comic)

After final assets are selected, run the packaging scripts rather than doing these steps manually:

```bash
python skills/story-video-factory/scripts/prepare_pure_comic_episode.py <episode>
```

- Caption text comes from `script.json` only. The render script enforces this; mismatched `caption-layout.json` causes a hard exit.
- For Douyin-native top captions, use `--caption-style douyin-msyh-top`; the style is defined in `references/caption-styles/douyin-msyh-top.json`.
- If a title cover exists at `assets/images/cover.png`, add `--include-cover` so the carousel starts with `00-cover.png`.
- Approved raw image sources belong in `selected-candidates.json`; do not guess from the first raw candidate.
- `output/publish/carousel/` is the Douyin upload folder, not `assets/images/`.
- QC report auto-fills objective fields (resolution, ratio, size); subjective fields require human review.
- Publish pack is a draft; always review titles and cover text before uploading.
- Sub-skill routing for post-production: `story-video-factory/scripts/` handles render, carousel, QC, and publish pack generation.
