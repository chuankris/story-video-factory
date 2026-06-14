"""Generate a Douyin publish pack skeleton for a pure comic episode.

Usage:
    python skills/story-video-factory/scripts/generate_publish_pack.py <episode_dir>
    python skills/story-video-factory/scripts/generate_publish_pack.py <episode_dir> --force
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def generate_pack(episode: Path, force: bool = False) -> None:
    meta = load_json(episode / "episode-meta.json")
    script_data = load_json(episode / "script.json")

    segments = script_data.get("segments")
    if segments is None:
        if isinstance(script_data, list):
            segments = script_data
        else:
            sys.exit("ERROR: script.json has no 'segments' key and is not a list.")

    panel_ids = [seg["id"] for seg in segments]
    texts = {seg["id"]: seg["text"] for seg in segments}

    title = meta.get("title", episode.name)
    episode_id = meta.get("episode_id", episode.name)
    first_text = texts.get(panel_ids[0], "") if panel_ids else ""
    last_text = texts.get(panel_ids[-1], "") if panel_ids else ""

    # Carousel file list
    carousel_dir = episode / "output" / "publish" / "carousel"
    carousel_files = sorted(carousel_dir.glob("*.png")) if carousel_dir.exists() else []
    carousel_list = "\n".join(
        f"{i+1}. `{f.name}`" for i, f in enumerate(carousel_files)
    ) or "# TODO: run build_publish_carousel.py first"

    # Upload order with caption preview
    panel_order = "\n".join(
        f"{i+1}. `{seq:02d}-{pid}.png` — {texts.get(pid, '')[:20]}..."
        for i, (seq, pid) in enumerate(zip(range(1, len(panel_ids)+1), panel_ids))
    )

    content = f"""# Douyin Publish Pack: {title}

Episode id: `{episode_id}`
Mode: pure comic carousel
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Images: `output/publish/carousel/`

---

## Title Options

> Edit these. Keep ≤20 characters. Pick one before uploading.

1. {title}
2. # TODO: 悬念问句 variant (e.g. 她把星星缝在背包上，多年后才明白为什么)
3. # TODO: 反差陈述 variant (e.g. 她嫌妈妈唠叨，后来却把那颗星星带去了远方)
4. # TODO: 情感钩子 variant based on last panel: {last_text[:20]}
5. # TODO: 5th option

Recommended: `{title}`

---

## Cover Text Options

> ≤8 chars main + ≤10 chars subtitle. Must be readable at thumbnail size.

1. 主线:（替换为8字以内）
   副线:（替换为10字以内）

2. # TODO: option 2

3. # TODO: option 3

Recommended cover image: first panel `01-{panel_ids[0] if panel_ids else "p001"}.png` or strongest emotional panel.

---

## Caption / 简介

> 2-4 lines: hook → context → interaction prompt → hashtags.
> Edit to match your voice before posting.

{first_text[:30] if first_text else "# TODO: opening hook"}

# TODO: 1-2 lines of context or emotional resonance.

你有没有一件小事，长大后才懂它的意义？评论区聊聊。

#温馨故事 #图文故事 #亲情 #治愈系漫画 #抖音图文

---

## Hashtags

- #温馨故事
- #图文故事
- #亲情
- #治愈系漫画
- #抖音图文
- # TODO: add 1-2 episode-specific tags

---

## Upload Order

{panel_order}

### Carousel files

{carousel_list}

---

## Risk Review

- violence/gore: # TODO: check
- superstition framing: # TODO: check (present as 民间故事/情感故事, not 宣扬)
- medical/legal/financial sensitive content: # TODO: check
- minors: # TODO: check (wholesome context expected)
- logos/brands/readable school names in images: # TODO: visual check
- generated text inside images: # TODO: verify captions are post-rendered (not model-generated)
- copyright music risk: use Douyin platform music library when adding music

---

## Posting Checklist

- [ ] Upload images from `output/publish/carousel/` in numeric order (see Upload Order above)
- [ ] Set cover image manually — do not rely on auto-selection
- [ ] Confirm title length ≤ 20 chars
- [ ] Confirm cover text readable at thumbnail size on mobile
- [ ] Confirm all caption cards readable after Douyin compression (check on phone)
- [ ] Add to series 合集 if applicable
- [ ] Record publish time and first-hour data in `series-log.md`

---

## Notes for Iteration

- # TODO: fill in after first-hour data.
"""

    out_path = episode / "output" / "publish" / "pack.generated.md"
    final_path = episode / "output" / "publish" / "pack.md"

    if final_path.exists() and not force:
        target = out_path
        print(f"NOTE: pack.md already exists. Writing to {out_path.name} (use --force to overwrite pack.md).")
    else:
        target = final_path if force else out_path

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"Publish pack written: {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Douyin publish pack skeleton for a pure comic episode.")
    parser.add_argument("episode", help="Path to episode directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing pack.md")
    args = parser.parse_args()

    episode = Path(args.episode)
    if not episode.is_dir():
        sys.exit(f"Episode directory not found: {episode}")

    generate_pack(episode, force=args.force)


if __name__ == "__main__":
    main()
