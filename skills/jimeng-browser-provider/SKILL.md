---
name: jimeng-browser-provider
description: Batch-generate comic panels and images on 即梦 (Jimeng, jimeng.jianying.com) via Playwright browser automation, since Jimeng has no public API/CLI. Use whenever the user wants to run image prompts through Jimeng, queue 跑图 batches, download generated images, or mentions 即梦/Jimeng/剪映生图. Also use to intake and rename downloaded Jimeng images into an episode's assets folder.
---

# Jimeng Browser Provider

## Reality Check (read first)

即梦 has no API. This skill drives the web UI (`https://jimeng.jianying.com`) with Playwright. Consequences:

- Selectors break when the site updates. Selectors live in `scripts/selectors.json`, NOT in code — when a run fails on a missing element, open the page, find the new selector, update that file, rerun. Do not patch the Python.
- Login is manual and human-owned. The script launches a **persistent profile** (`--profile` dir); first run, the user logs in by hand, the session then persists.
- The user stays in the loop for credit spend and content review. Automation only removes typing/clicking drudgery — never design around bypassing limits.

## Setup (once)

```bash
pip install playwright
playwright install chromium
python scripts/jimeng_run.py login --profile .jimeng-profile
# → browser opens; user logs in manually, then closes the window
```

Keep `.jimeng-profile/` out of git (contains session cookies) — it is in the repo `.gitignore`.

## Batch Generation Workflow

1. Input: `prompts.json` — `[{"id": "1", "prompt": "...", "count": 1}]`. Build it from the storyboard; one entry per panel; include the episode's fixed style prefix in every prompt (character + art-style block) for consistency.
2. Confirm with the user: number of prompts × credits each ≈ total credit spend this run.
3. Run: `python scripts/jimeng_run.py generate --profile .jimeng-profile --prompts prompts.json --outdir assets/images-raw/`
   - Headed mode by default — the user can watch and abort.
   - The script verifies the prompt landed intact in the editor (CJK input can silently corrupt — it aborts before spending credits if so), submits, waits, and downloads results detected by CDN domain + rendered size, not fragile container selectors.
   - **HD downloads**: the visible `<img src>` is only a ~270px display thumbnail. Per image the script clicks the thumbnail to open the preview modal, then (a) clicks the modal's download control (browser download = original file), else (b) fetches the largest non-thumbnail image rendered in the modal, else (c) falls back to the thumbnail src. Every file is measured (pure-Python png/jpg/webp header parse); if any file's longest side is under `min_download_long_px` (default 1024, selectors.json) the entry is `low_resolution`, not `downloaded` — `generate` skips it without re-spending credits, `resume` retries the HD fetch. State records `width/height/bytes/content_type/source_url/method` per file; check `method` to see which path actually delivered (`preview_download` / `preview_src` / `thumbnail_fallback`).
   - **Scoped collection**: images are searched only inside the newest result card (`result_scope` selectors) and capped at `max_results_per_task` — a `resume` on an old workspace must not sweep up the whole conversation history.
   - Filenames use `<id>_001.webp`-style zero-padded numbering (alphabetic suffixes break past 26 files on Windows); download filenames from the site are sanitized and extension-whitelisted.
   - prompts.json reserves `reference_image` / `image_to_image` fields for future image-to-image with a GPT-image style anchor; they are accepted and ignored today.
   - State is per-batch: `<prompts-stem>.jimeng-state.json` next to the prompts file (`--state` to override). Each entry tracks `pending → submitted → confirmed → downloaded / failed` plus the `workspace_url`. Rerunning skips downloaded ids.
4. Video: add `--video`. Two differences from images: a credit-cost confirm dialog (继续生成) must be clicked — nothing is spent until then — and results live in hidden `<video>` tags detected by URL markers.
5. Slow renders: if a run times out, the workspace URL is saved; `python scripts/jimeng_run.py resume --prompts ... --outdir ...` reopens it later and downloads finished results at zero cost.
6. Selection: show the user candidates per panel; copy the chosen one to `assets/images/<id>.png`. Never auto-pick — composition quality lives or dies here.

## Failure Handling

- Element not found → screenshot is saved to `jimeng-errors/`; inspect it, fix `selectors.json`, rerun (completed ids skip automatically).
- Login expired → script detects login wall and exits asking for `login` mode rerun.
- Credit exhausted → stop, report which ids remain, suggest splitting across days or routing remaining panels to GPT-image.
- Content blocked by platform review → rewrite that prompt (usually weapons/blood words); keep a `prompt-rewrites.md` note so the same trap is avoided next episode.

## Scripts

- `scripts/jimeng_run.py` — `login` and `generate` subcommands. Requires `playwright`.
- `scripts/selectors.json` — CSS/text selectors for the Jimeng UI; the only file to touch when the site changes.

UI facts the scripts rely on (verified 2026-06): `/ai-tool/image/generate` redirects to `/ai-tool/home`, where the 图片生成/视频生成 mode card must be clicked; the prompt box is a contenteditable ProseMirror editor (no `<textarea>`); `class*=submit-butt` matches multiple buttons of which some are hidden — the script picks the first visible+enabled match, never `.first`; after submit the page moves to `/ai-tool/generate?workspace=...` where results render; real images come from `dreamina-sign.byteimg.com`; real videos sit in non-visible `<video>` tags with `vlabvod.com` / `mime_type=video_mp4` URLs (the loading animation is also an mp4 — excluded by `record-loading-animation`).

## Smoke Test (no credits)

`python tests/smoke_jimeng.py` (repo root) opens the site with a fresh logged-out profile and asserts the login wall is detected — proving generate would stop before spending credits. Run it after any selectors.json update.

## References

- `references/automation-notes.md`: selector update procedure, prompt style-prefix pattern, anti-detection etiquette.
