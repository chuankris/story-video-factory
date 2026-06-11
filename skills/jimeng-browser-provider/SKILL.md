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
   - The script submits each prompt, waits for results, downloads all candidate images as `<id>_a.png`, `<id>_b.png`, ...
   - State is checkpointed to `jimeng-state.json`; rerunning skips completed ids.
4. Selection: show the user candidates per panel; copy the chosen one to `assets/images/<id>.png`. Never auto-pick — composition quality lives or dies here.

## Failure Handling

- Element not found → screenshot is saved to `jimeng-errors/`; inspect it, fix `selectors.json`, rerun (completed ids skip automatically).
- Login expired → script detects login wall and exits asking for `login` mode rerun.
- Credit exhausted → stop, report which ids remain, suggest splitting across days or routing remaining panels to GPT-image.
- Content blocked by platform review → rewrite that prompt (usually weapons/blood words); keep a `prompt-rewrites.md` note so the same trap is avoided next episode.

## Scripts

- `scripts/jimeng_run.py` — `login` and `generate` subcommands. Requires `playwright`.
- `scripts/selectors.json` — CSS/text selectors for the Jimeng UI; the only file to touch when the site changes.

## References

- `references/automation-notes.md`: selector update procedure, prompt style-prefix pattern, anti-detection etiquette.
