# MiniMax API Notes

Verified against platform docs as of 2026-06. If a request fails with an unknown-field or model-not-found error, re-check https://platform.minimax.io/docs (global) or https://platform.minimaxi.com (mainland) — names move fast.

## Hosts

- Mainland: `https://api.minimaxi.chat` (default in scripts)
- Global: `https://api.minimax.io`
- US West: `https://api-uw.minimax.io`

Key and GroupId come from the platform console; they differ between mainland and global accounts.

## TTS — `POST /v1/t2a_v2?GroupId=<id>`

- Models: `speech-2.8-hd` (quality), `speech-2.8-turbo` (speed/cost). Older `speech-02-hd` may still work.
- Body: `model`, `text` (≤10k chars), `stream:false`, `voice_setting{voice_id,speed,vol,pitch}`, `audio_setting{sample_rate,bitrate,format,channel}`.
- Response: `data.audio` is **hex-encoded** audio bytes (not base64).
- Voice ids: hundreds of system voices + clones. Storyteller-ish starting points: `audiobook_male_1`, `audiobook_male_2`, `male-qn-jingying`. List voices via the platform console.

## Image — `POST /v1/image_generation`

- Model: `image-01`. Synchronous.
- Body: `model`, `prompt`, `aspect_ratio` (16:9/4:3/3:2/2:3/3:4/9:16/21:9), `n` (≤9), `response_format` (`base64` or `url`).
- Subject reference (character consistency): `"subject_reference": [{"type": "character", "image_file": "<data-url or url>"}]`.
- Rate limit ~10 RPM; space batch requests ≥6s apart.
- Response: `data.image_base64` array (base64 mode) or `data.images` URLs.

## Video — async, three steps

1. `POST /v1/video_generation` — body: `model`, `prompt`, optional `first_frame_image` (data URL), `duration` (6/10), `resolution` (`768P`/`1080P`). Returns `task_id`.
   - Models: `MiniMax-Hailuo-02`, `MiniMax-Hailuo-2.3`; `S2V-01` for subject-reference mode.
2. `GET /v1/query/video_generation?task_id=<id>` — `status`: `Queueing|Preparing|Processing|Success|Fail`. On `Success`, returns `file_id`.
3. `GET /v1/files/retrieve?GroupId=<id>&file_id=<id>` — returns `file.download_url` (URL expires; download promptly).

Generation takes minutes. Poll at ≥30s intervals.

## Prompting Hailuo for story shots

- One action per clip; 6s holds one camera move + one subject action well.
- Specify camera explicitly: `[Push in]`, `[Pan left]`, `[Tracking shot]` bracket syntax is supported.
- For comic-style consistency, prefer image-to-video with a panel as `first_frame_image` over pure text-to-video.
