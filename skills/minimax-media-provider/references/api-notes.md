# MiniMax API Notes

Verified against platform docs as of 2026-06. If a request fails with an unknown-field or model-not-found error, re-check https://platform.minimax.io/docs (global) or https://platform.minimaxi.com (mainland) — names move fast.

## Hosts

- Mainland: `https://api.minimaxi.com` (default in scripts; backup `https://api-bj.minimaxi.com`)
- Global: `https://api.minimax.io` / US West `https://api-uw.minimax.io`

Auth is Bearer `MINIMAX_API_KEY` only — current endpoints take **no GroupId** anywhere. Keys differ between mainland and global accounts.

## TTS — `POST /v1/t2a_v2`

- Models: `speech-2.8-hd` (quality), `speech-2.8-turbo` (speed/cost); 2.6/02/01 series still accepted.
- Body: `model`, `text` (≤10k chars), `stream:false`, `voice_setting{voice_id,speed,vol,pitch,emotion?}`, `audio_setting{sample_rate,bitrate,format,channel}`.
- Response: `data.audio` is **hex-encoded** audio bytes (not base64).
- Voice ids: query via the voice-management API or the 系统音色列表 FAQ on the platform. Mandarin storyteller starting point: `male-qn-qingse`-family or an `audiobook_male_*` legacy id; pick once per IP and pin it.
- Useful extras (see official OpenAPI):
  - `pronunciation_dict.tone`: `["处理/(chu3)(li3)"]` fixes 多音字 without rewriting the script.
  - Pause control inline: `<#0.5#>` inserts a 0.5s pause — good for 说书 beats.
  - `subtitle_enable: true` returns sentence-level timestamp JSON — can replace ffprobe-based alignment in comic-video-composer someday.
  - speech-2.8 supports interjection tags like `(laughs)`, `(sighs)` — sparing use fits 说书人.

## Image — `POST /v1/image_generation`

- Model: `image-01`. Synchronous.
- Body: `model`, `prompt`, `aspect_ratio` (16:9/4:3/3:2/2:3/3:4/9:16/21:9), `n` (≤9), `response_format` (`base64` or `url`).
- Subject reference (character consistency): `"subject_reference": [{"type": "character", "image_file": "<data-url or url>"}]`.
- Rate limit ~10 RPM; space batch requests ≥6s apart.
- Response: `data.image_base64` array (base64 mode) or `data.images` URLs.

## Video — async, three steps

1. `POST /v1/video_generation` — body: `model`, `prompt` (≤2000 chars), optional `first_frame_image` (data URL), `duration` (6/10), `resolution` (`768P`/`1080P`), `prompt_optimizer` (default true). Returns `task_id`.
   - Models: `MiniMax-Hailuo-2.3`, `MiniMax-Hailuo-02`, `T2V-01-Director`, `T2V-01`; `S2V-01` for subject-reference mode.

**Aspect ratio — critical for Douyin.** T2V has NO vertical/aspect parameter: `768P` returns 1366x768, `1080P` returns 1920x1080, both 16:9 landscape. To get 9:16 vertical:
   - **Preferred**: image-to-video with a 9:16 `first_frame_image` (e.g. a comic panel) — output follows the input image's aspect ratio.
   - **Fallback**: accept 16:9 and convert in the composer (center-crop or blur-pad; recipes in comic-video-composer's `composition-spec.md`). Crop loses ~2/3 of the frame width — compose the prompt with a centered subject if this route is planned.
2. `GET /v1/query/video_generation?task_id=<id>` — `status`: `Queueing|Preparing|Processing|Success|Fail`. On `Success`, returns `file_id`.
3. `GET /v1/files/retrieve?file_id=<id>` — returns `file.download_url` (URL expires; download promptly).

Generation takes minutes. Poll at ≥30s intervals.

## Prompting Hailuo for story shots

- One action per clip; 6s holds one camera move + one subject action well.
- Camera control uses bracket commands (15 supported, mainland docs use Chinese): [左移] [右移] [左摇] [右摇] [推进] [拉远] [上升] [下降] [上摇] [下摇] [变焦推近] [变焦拉远] [晃动] [跟随] [固定]. Combine ≤3 inside one bracket ([左摇,上升]); sequential brackets fire in order.
- Set `prompt_optimizer: false` only when exact control matters; default rewriting usually helps.
- For comic-style consistency AND vertical output, prefer image-to-video with a 9:16 panel as `first_frame_image` over pure text-to-video.
