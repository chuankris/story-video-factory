# Workflow

Use this reference to decide the current production state and next artifact.

## States

- `idea`: topic, source, or platform direction is still being chosen.
- `outline_review`: story outline is being drafted or revised.
- `script_review`: narration script is being drafted or revised.
- `storyboard_review`: shot or panel plan is being drafted or revised.
- `prompt_review`: provider-specific prompts are being prepared.
- `asset_generation`: user or automation is generating images/video/audio.
- `asset_intake`: generated assets are being checked and renamed.
- `composition`: draft video is being assembled.
- `quality_review`: draft is being checked for content, timing, audio, and platform fit.
- `publishing_pack`: title, cover text, caption, tags, and release notes are being prepared.

## Review Gates

Do not advance past these gates without user approval or an explicit instruction to experiment:

- Outline before script.
- Script before storyboard.
- Storyboard before prompts.
- Final assets before composition.
- Draft video before publishing pack.

## Parallel Production

When one episode is rendering or waiting for image generation, use the time to advance another episode only through review-safe states:

- outline review
- script review
- storyboard review
- prompt review

Avoid starting composition for an episode whose final images have not been handed off.

## Artifact Naming

Prefer versioned review files:

- `outline_v1_for_review.md`
- `script_v2_for_review.json`
- `storyboard_v1_for_review.json`
- `prompts_v1_for_review.json`

Promote a review artifact to the production filename only after acceptance.
