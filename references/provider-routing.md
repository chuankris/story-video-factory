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

GPT-image:

- style references
- character references
- key frames
- controlled image generation when available

Minimax:

- narration TTS
- generated video clips when quota should be spent on high-value shots

Jimeng:

- batch image generation through manual or browser-assisted workflow
- useful for comic panels and stylistic image batches

Local tools:

- MoviePy or FFmpeg composition
- subtitle rendering
- file checks
- audio/video quality checks

## Mode Defaults

For `comic-video`:

- Images: Jimeng, GPT-image, or mixed.
- Audio: Minimax TTS when available.
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

## Browser Automation

Use browser automation only to reduce repetitive UI work for providers that lack CLI/API access. Keep the user in the loop for login, quota, content review, and final selection.

Do not design workflows around bypassing membership limits or platform restrictions.
