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


def _clauses(text: str) -> list[str]:
    """Split text on CJK punctuation, return non-empty stripped clauses."""
    result = []
    current = ""
    for ch in text:
        current += ch
        if ch in "，。！？、；":
            c = current.rstrip("，。！？、；").strip()
            if c:
                result.append(c)
            current = ""
    if current.strip():
        result.append(current.strip())
    return result


def derive_titles(title: str, texts: dict[str, str], panel_ids: list[str]) -> list[str]:
    """Generate 5 real title candidates from episode data. All ≤20 chars."""
    options: list[str] = [title]

    # Option 2: key clause from last panel (the emotional payoff)
    if panel_ids:
        last = texts.get(panel_ids[-1], "")
        for c in reversed(_clauses(last)):
            if 4 <= len(c) <= 20 and c != title:
                options.append(c)
                break
        if len(options) == 1 and last:
            options.append(last[:20].rstrip("，。！？"))

    # Option 3: first clause of first panel (the hook)
    if panel_ids:
        first = texts.get(panel_ids[0], "")
        for c in _clauses(first):
            if 4 <= len(c) <= 20 and c not in options:
                options.append(c)
                break
        if len(options) == 2 and first:
            options.append(first[:20].rstrip("，。！？"))

    # Option 4: contracted title (drop first 2 chars if title is long)
    if len(title) > 8:
        contracted = title[2:]
        if 5 <= len(contracted) <= 20 and contracted not in options:
            options.append(contracted)
    if len(options) == 3:
        options.append(title + "的故事" if len(title) <= 16 else title[-10:])

    # Option 5: key clause from middle panel
    if panel_ids and len(panel_ids) >= 3:
        mid_text = texts.get(panel_ids[len(panel_ids) // 2], "")
        for c in _clauses(mid_text):
            if 4 <= len(c) <= 20 and c not in options:
                options.append(c)
                break
    if len(options) < 5:
        # Pad with last-panel full first 20 chars if still short
        last = texts.get(panel_ids[-1], "") if panel_ids else ""
        if last and last[:18] not in options:
            options.append(last[:18].rstrip("，。！？"))

    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for o in options:
        if o not in seen:
            seen.add(o)
            unique.append(o)

    return unique[:5]


def derive_covers(title: str, texts: dict[str, str], panel_ids: list[str]) -> list[tuple[str, str]]:
    """Generate 3 cover text candidates (main ≤8 chars, subtitle ≤10 chars)."""
    covers: list[tuple[str, str]] = []

    # Option 1: natural split of the title
    split = min(6, len(title) // 2 + 1)
    main1, sub1 = title[:split], title[split:]
    covers.append((main1[:8], sub1[:10]))

    # Option 2: key phrase from last panel
    if panel_ids:
        last = texts.get(panel_ids[-1], "")
        last_clauses = _clauses(last)
        if len(last_clauses) >= 2:
            main2 = last_clauses[-1][:8]
            sub2 = last_clauses[-2][:10]
            covers.append((main2, sub2))
        elif last_clauses:
            main2 = last_clauses[0][:8]
            covers.append((main2, last[len(last_clauses[0]):].rstrip("，。！？")[:10]))

    # Option 3: from first panel
    if panel_ids:
        first = texts.get(panel_ids[0], "")
        first_clauses = _clauses(first)
        if first_clauses:
            main3 = first_clauses[0][:8]
            sub3 = first_clauses[1][:10] if len(first_clauses) > 1 else ""
            if (main3, sub3) not in covers:
                covers.append((main3, sub3))

    while len(covers) < 3:
        covers.append((f"（主线{len(covers)+1}）", f"（副线{len(covers)+1}）"))

    return covers[:3]


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

    title_options = derive_titles(title, texts, panel_ids)
    cover_options = derive_covers(title, texts, panel_ids)

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

{chr(10).join(f"{i+1}. {opt}" for i, opt in enumerate(title_options))}

Recommended: `{title_options[0]}`

---

## Cover Text Options

> ≤8 chars main + ≤10 chars subtitle. Must be readable at thumbnail size.

{chr(10).join(f"{i+1}. 主线: {m}\\n   副线: {s}" for i, (m, s) in enumerate(cover_options))}

Recommended cover image: first panel `01-{panel_ids[0] if panel_ids else "p001"}.png` or strongest emotional panel.

---

## Caption / 简介

> 2-4 lines: hook → context → interaction prompt → hashtags.
> Edit to match your voice before posting.

{last_text[:40].rstrip("，。！？") if last_text else first_text[:40].rstrip("，。！？") if first_text else title}

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
