---
name: story-video-factory
description: Orchestrate reviewed story-to-video production for Douyin and similar short-video platforms. Use when the user wants to plan a content factory, turn stories into comics or videos, choose between image/video/TTS providers, manage outline/script/storyboard/prompt/asset/composition states, or coordinate sub-skills. Always use this skill first when the user mentions making a story video, comic video, episode production, or asks "what's next" in a video production pipeline — it decides which sub-skill handles each step.
---

# Story Video Factory (Director)

## Role

Act as the production director for story-based short videos.

This skill coordinates the whole workflow. It does not replace specialized style or provider skills. Use it to decide what should happen next, which provider or sub-skill should be used, and what artifact should be produced for review.

## Core Workflow

Always preserve the review-first order:

1. Select topic or story source.
2. Produce story outline for review.
3. Produce narration script for review.
4. Produce storyboard for review.
5. Produce asset prompts and provider plan.
6. Generate or collect assets.
7. Produce TTS and compose draft video.
8. Quality-check draft video.
9. Prepare publishing pack.

Do not skip from script ideas to video generation unless the user explicitly asks for a rough experiment.

## Production Modes

Choose one mode before routing providers:

- `pure_comic`: static comic panel carousel, post-rendered captions, no audio or video.
- `comic_to_video`: approved pure comic images plus narration, subtitles, and camera motion.
- `direct_video`: generated video clips (Hailuo/MiniMax) assembled into a short video.
- `hybrid`: comic images for most beats, generated video for hook/reveal shots.

Prefer `pure_comic` for stable daily production. Use `hybrid` when limited video-generation quota should be saved for important shots.

## Sub-Skill Routing

Route each step to its specialized skill:

| Step | Skill |
| --- | --- |
| 初刻拍案惊奇 / 说书体 narration, episode review | `chuke-storytelling-video` |
| Comic panels via Jimeng (browser automation) | `jimeng-browser-provider` |
| Key frames / style refs via GPT-image (Codex only) | `gpt-image-provider` |
| Narration TTS, generated video clips | `minimax-media-provider` |
| Image-to-video composition, subtitles, QC | `comic-video-composer` |
| Title, cover, caption, tags, release checklist | `douyin-publisher-pack` |

If a sub-skill is not available in the current environment, continue with the matching reference in this skill and keep the artifact reviewable.

## References

Load only what is needed:

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

```
python skills/story-video-factory/scripts/prepare_pure_comic_episode.py <episode>
```

- Caption text comes from `script.json` only. The render script enforces this — mismatched `caption-layout.json` causes a hard exit.
- `output/publish/carousel/` is the Douyin upload folder, not `assets/images/`.
- QC report auto-fills objective fields (resolution, ratio, size); subjective fields require human review.
- Publish pack is a template — always edit titles and cover text before uploading.
- Sub-skill routing for post-production: `story-video-factory/scripts/` handles render, carousel, QC, and publish pack generation.
