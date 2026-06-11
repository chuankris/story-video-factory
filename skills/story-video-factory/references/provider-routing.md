# Provider Routing

Use this reference to choose which tool should handle each media task.

## Available Provider Roles

GPT / Codex:

- concept development
- outline and script drafting
- storyboard planning
- prompt engineering
- local file management
- composition scripts and quality checks

GPT-image (Codex environment only — see `gpt-image-provider` skill):

- style references
- character references
- key frames
- controlled image generation when available

Minimax (API, key required — see `minimax-media-provider` skill):

- narration TTS
- image generation (image-01) with subject reference for character-consistent panels
- generated video clips when quota should be spent on high-value shots

Jimeng (browser automation via Playwright — see `jimeng-browser-provider` skill):

- batch image generation through browser-assisted workflow
- useful for comic panels and stylistic image batches

Local tools (see `comic-video-composer` skill):

- MoviePy or FFmpeg composition
- subtitle rendering
- file checks
- audio/video quality checks

## Mode Defaults

For `comic-video`:

- Images: Jimeng, GPT-image, or mixed.
- Audio: Minimax TTS.
- Video: local composition.

For `image-comic`:

- Images: Jimeng or GPT-image.
- Output: panels, cover, caption.

For `ai-video`:

- Video: Minimax or another video provider.
- Use quota for hooks, reveals, or scenes requiring motion.

For `hybrid`:

- Use images for most story beats.
- Use generated video for 1-3 high-impact moments.
- Compose everything locally.

## Quota Awareness

Before generating, check the cheapest provider that meets quality needs:

1. Comic panels in bulk (scenery, props, crowds) → Jimeng (monthly credits, browser automation).
2. Main-character panels needing consistency → Minimax image-01 with subject reference, or GPT-image (Codex only).
3. Motion shots → Minimax video (about 3 videos/day on TokenPlanMax — spend on hook/reveal only).
4. All narration audio → Minimax TTS (cheap relative to video; batch by episode).

Record what was spent per episode in a simple `quota-log.md` so daily limits are not hit mid-episode.

## Browser Automation

Use browser automation only to reduce repetitive UI work for providers that lack CLI/API access. Keep the user in the loop for login, quota, content review, and final selection.

Do not design workflows around bypassing membership limits or platform restrictions.
