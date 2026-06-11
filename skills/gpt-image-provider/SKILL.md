---
name: gpt-image-provider
description: Generate style references, character sheets, and precise key frames with GPT-image using ChatGPT membership quota. Codex environment only — in other harnesses, route image work to jimeng-browser-provider instead. Use when running inside Codex and the user needs character consistency references, a style anchor image, cover art, or a key frame that Jimeng cannot render precisely.
---

# GPT-Image Provider (Codex only)

## Environment Gate

This skill assumes the Codex environment, where GPT-image generation is available natively through the ChatGPT membership. **If you are not running in Codex** (e.g., Claude Code / Cowork), do not attempt to call GPT-image: say so, and route the request to `jimeng-browser-provider` (bulk panels) or ask the user to generate the image in the ChatGPT app and drop the file into the episode's `assets/` folder.

## What GPT-image Is For (vs Jimeng)

Spend membership quota only where precision beats volume:

- **Character sheet**: one front/side/three-quarter reference per main character, generated once per IP and reused as the style anchor in all Jimeng prompts.
- **Style anchor**: 1-2 images defining the IP's art style; describe them verbatim in the Jimeng style prefix.
- **Covers and key frames**: the episode cover and the hook panel, where text layout space and exact composition matter.
- **Fix-ups**: a panel Jimeng repeatedly fails (complex hands, specific props).

Everything bulk goes to Jimeng.

## Workflow

1. Write the image request as a full natural-language prompt (GPT-image follows long descriptive prompts well; no tag-style prompting needed).
2. Always specify: aspect ratio (3:4 panels, 9:16 covers), 无文字 unless text is wanted, and the era/costume constraints for historical stories.
3. Generate, then save into the episode tree: `assets/refs/<name>.png` for references, `assets/images/<segment-id>.png` for panels.
4. Record in `quota-log.md`: date, what, why GPT-image instead of Jimeng.

## Character Consistency Recipe

1. Generate the character sheet once: "三视图 character sheet, <description>, 白底, 无文字".
2. For later images of the same character, attach/reference the sheet image in the request and repeat the same textual description anyway — text + image reference together hold consistency best.
3. Keep all character descriptions in the IP's `characters.md` so wording never drifts between episodes.
