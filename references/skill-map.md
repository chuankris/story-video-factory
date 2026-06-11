# Skill Map

Use this reference when evolving the big-skill / small-skill architecture.

## Current Skill

`story-video-factory` is the director skill. It owns workflow, state, mode selection, provider routing, and handoff rules.

## Existing Sub-Skill

`chuke-storytelling-video` handles 初刻拍案惊奇, classical storyteller narration, and the reviewed 上集/中集/下集 workflow.

## Planned Sub-Skills

`comic-video-composer`:

- image-to-video composition
- subtitles
- TTS alignment
- video quality checks

`minimax-media-provider`:

- Minimax TTS
- Minimax video generation
- quota-aware provider use

`jimeng-browser-provider`:

- browser-assisted Jimeng image generation
- prompt queueing
- download and file intake

`douyin-publisher-pack`:

- title generation
- cover text
- captions
- hashtag and risk review

## Architecture Rule

Keep `story-video-factory` light. Put provider-specific API details, browser automation steps, style rules, and composition scripts in specialized skills.
