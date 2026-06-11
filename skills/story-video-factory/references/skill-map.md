# Skill Map

Use this reference when evolving the big-skill / small-skill architecture.

## Director Skill

`story-video-factory` owns workflow, state, mode selection, provider routing, and handoff rules.

## Sub-Skills (all in `skills/` of this plugin)

`chuke-storytelling-video`:

- 初刻拍案惊奇 and classical storyteller narration
- reviewed 上集/中集/下集 episode workflow

`comic-video-composer`:

- image-to-video composition (FFmpeg/MoviePy)
- subtitles and TTS alignment
- video quality checks

`minimax-media-provider`:

- Minimax TTS (API)
- Minimax/Hailuo video generation (API)
- quota-aware provider use

`jimeng-browser-provider`:

- Playwright-assisted Jimeng image generation
- prompt queueing
- download and file intake

`gpt-image-provider`:

- GPT-image generation for style refs and key frames
- Codex environment only

`douyin-publisher-pack`:

- title generation
- cover text
- captions
- hashtag and risk review

## Architecture Rule

Keep `story-video-factory` light. Put provider-specific API details, browser automation steps, style rules, and composition scripts in specialized skills.
