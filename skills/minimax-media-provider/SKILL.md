---
name: minimax-media-provider
description: Generate narration TTS audio, images, and AI video clips through the MiniMax (海螺/Hailuo) API. Use whenever the user wants TTS, 配音, voiceover, narration audio, AI 视频生成, Hailuo video, image-01 生图, character-consistent panels via subject reference, or mentions MiniMax/海螺 quota. Also use when a script needs to be batch-converted to per-segment audio files, or when 1-3 high-impact motion shots need to be generated from prompts or first-frame images.
---

# Minimax Media Provider

## Prerequisites

Environment variables (never hardcode, never print):

- `MINIMAX_API_KEY` — required.
- `MINIMAX_GROUP_ID` — required for TTS.
- `MINIMAX_API_HOST` — optional; defaults to `https://api.minimaxi.chat` (mainland). Use `https://api.minimax.io` for the global platform.

If a variable is missing, stop and ask the user to set it; do not invent values.

## Quota Rules (TokenPlanMax monthly plan)

- Video: ~3 generated videos per day. Never batch-generate video; confirm each clip with the user before submitting, and only for hook/reveal/high-impact shots (see director skill's provider routing).
- TTS: cheap by comparison — batch a whole episode in one run, but reuse existing audio: skip any segment whose output file already exists unless `--force`.
- Log every spend to the episode's `quota-log.md` (what, when, prompt summary).

## TTS Workflow

1. Input: `script.json` (segments with `id` + `text`).
2. Run `scripts/minimax_tts.py --script <script.json> --outdir <episode>/assets/audio/`.
3. Output: `<id>.mp3` per segment.
4. Spot-check: play/probe 2-3 files; wrong pronunciation → fix the script text (homophone rewrite per the chuke style guide), not the voice settings, then regenerate only those ids with `--ids`.

Default voice settings live at the top of the script (model `speech-2.8-hd`, a male storyteller voice, speed 1.0). Change via CLI flags; record the chosen voice in the episode dir so all episodes of one IP sound identical.

## Video Workflow (async)

1. Confirm with user: shot description, duration, model, today's remaining quota.
2. Submit: `scripts/minimax_video.py submit --prompt "..." [--image first_frame.png] [--model MiniMax-Hailuo-02]` → prints `task_id`, saved to `video-tasks.json`.
3. Poll: `scripts/minimax_video.py poll` — checks all pending tasks, downloads finished videos to `assets/video/<task_id>.mp4`.
4. While waiting (minutes), continue other review-safe work; do not block.

## Image Workflow (image-01)

Use for panels needing **character consistency**: image-01 supports a subject reference image, which prompt-only providers (Jimeng) cannot do.

1. Generate or pick one clean character reference image (face clearly visible); keep it at `assets/refs/<character>.png`.
2. Batch: `scripts/minimax_image.py --prompts prompts.json --outdir assets/images-raw --aspect 3:4 --subject assets/refs/<character>.png`
   - Same `prompts.json` format as the Jimeng skill, so a batch can be re-routed between providers without rework.
   - Skips completed ids on rerun; respects the ~10 RPM limit.
3. Selection stays human: show candidates, copy chosen into `assets/images/<id>.png`.
4. Check the plan's image quota in the platform console before large batches; log spend to `quota-log.md`.

Routing rule of thumb: panels featuring the main character → image-01 with subject reference; scenery/props/crowd panels → Jimeng credits.

## Failure Handling

- HTTP 429 / quota errors: report remaining work, stop submitting, suggest tomorrow's plan. Do not retry-loop.
- TTS returns silence/garbage for a segment: usually illegal chars in text — strip emoji/Latin abbreviations and retry that id once.
- Video task `Fail` status: report the reason; one prompt rewrite attempt max before asking the user.

## Scripts

- `scripts/minimax_tts.py` — batch TTS from script.json. Pure stdlib.
- `scripts/minimax_image.py` — image-01 generation, single or batch, optional subject reference. Pure stdlib.
- `scripts/minimax_video.py` — submit/poll video generation tasks. Pure stdlib.

## References

- `references/api-notes.md`: endpoints, request/response shapes, voice & model ids.
