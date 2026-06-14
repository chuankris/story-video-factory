"""Batch caption renderer for pure comic episodes.

Usage:
    python skills/story-video-factory/scripts/render_lettered_panels.py <episode_dir>
    python skills/story-video-factory/scripts/render_lettered_panels.py <episode_dir> --panel p003
    python skills/story-video-factory/scripts/render_lettered_panels.py <episode_dir> --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920

FONT_PATHS = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
]


def make_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise RuntimeError(
        "No CJK font found. Install Microsoft YaHei (msyh.ttc) or SimHei (simhei.ttf)."
    )


def load_script(episode: Path) -> dict[str, str]:
    raw = (episode / "script.json").read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    segments = data.get("segments", data if isinstance(data, list) else [])
    result = {}
    for seg in segments:
        try:
            result[seg["id"]] = seg["text"]
        except KeyError:
            print(f"WARNING: skipping malformed segment in script.json: {seg}")
    return result


def load_caption_layout(episode: Path) -> dict[str, dict]:
    layout_path = episode / "caption-layout.json"
    if not layout_path.exists():
        return {}
    raw = json.loads(layout_path.read_text(encoding="utf-8-sig"))
    result: dict[str, dict] = {}
    for panel_id, value in raw.items():
        if isinstance(value, list):
            result[panel_id] = {"lines": value, "source": None}
        elif isinstance(value, dict):
            result[panel_id] = {"lines": value["lines"], "source": value.get("source")}
        else:
            print(f"WARNING: caption-layout.json entry for {panel_id} has unknown format, skipping")
    return result


def auto_wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Greedy character-level wrap, preferring to break after CJK punctuation."""
    BREAK_AFTER = set("，。！？、；：")
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if font.getlength(candidate) <= max_width:
            current = candidate
            if char in BREAK_AFTER and font.getlength(current) > max_width * 0.55:
                lines.append(current)
                current = ""
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines or [text]


def find_raw_source(episode: Path, panel_id: str) -> Path | None:
    candidates = sorted((episode / "assets" / "images-raw").glob(f"{panel_id}_*.png"))
    return candidates[0] if candidates else None


def render_panel(
    episode: Path,
    panel_id: str,
    script_text: str,
    lines: list[str],
    source: Path,
    dry_run: bool = False,
) -> Path:
    joined = "".join(lines)
    if joined != script_text:
        print(f"ERROR: caption-layout lines for {panel_id} do not match script.json")
        print(f"  script : {script_text!r}")
        print(f"  layout : {joined!r}")
        sys.exit(1)

    out = episode / "assets" / "images" / f"{panel_id}.png"
    page_num = panel_id.removeprefix("p").lstrip("0") or "0"
    page_label = page_num.zfill(2)

    if dry_run:
        print(f"[dry-run] {panel_id}: {source} -> {out}  lines={lines}")
        return out

    img = Image.open(source).convert("RGB")
    scale = max(W / img.width, H / img.height)
    img = img.resize(
        (int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS
    )
    left = (img.width - W) // 2
    top = (img.height - H) // 2
    base = img.crop((left, top, left + W, top + H)).convert("RGBA")

    # Bottom gradient
    fade_h = 420
    grad = Image.new("RGBA", (W, fade_h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(fade_h):
        alpha = int(95 * (y / fade_h) ** 1.6)
        gd.line((0, y, W, y), fill=(35, 24, 16, alpha))
    base.alpha_composite(grad, (0, H - fade_h))

    body = make_font(35)
    small = make_font(22)

    # Card shadow
    card_w = 900
    card_h = max(166, 28 + len(lines) * 48 + 20)
    card_x = (W - card_w) // 2
    card_y = H - 238
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (card_x + 8, card_y + 12, card_x + card_w + 8, card_y + card_h + 12),
        radius=22,
        fill=(0, 0, 0, 82),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(13))
    base.alpha_composite(shadow)

    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle(
        (card_x, card_y, card_x + card_w, card_y + card_h),
        radius=24,
        fill=(255, 250, 235, 232),
        outline=(219, 188, 120, 185),
        width=2,
    )
    # Accent dot
    cx, cy = card_x + 48, card_y + 48
    draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(195, 147, 54, 255))

    text_x = card_x + 75
    text_y = card_y + 28
    for i, line in enumerate(lines):
        draw.text((text_x, text_y + i * 48), line, fill=(61, 52, 40, 255), font=body)
    draw.text(
        (card_x + card_w - 50, card_y + card_h - 34),
        page_label,
        fill=(120, 105, 82, 210),
        font=small,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out)
    return out


def process_episode(episode: Path, only_panel: str | None = None, dry_run: bool = False) -> None:
    scripts = load_script(episode)
    layout = load_caption_layout(episode)

    body_font = make_font(35)
    text_area_width = 900 - 75 - 20  # card_w - left_margin - right_padding

    panel_ids = list(scripts.keys())
    if only_panel:
        if only_panel not in scripts:
            sys.exit(f"ERROR: panel id '{only_panel}' not found in script.json")
        panel_ids = [only_panel]

    errors = 0
    for panel_id in panel_ids:
        script_text = scripts.get(panel_id)
        if script_text is None:
            print(f"WARNING: {panel_id} not found in script.json, skipping")
            continue

        # Resolve lines and source
        if panel_id in layout:
            entry = layout[panel_id]
            lines = entry["lines"]
            raw_source_override = entry["source"]
        else:
            lines = auto_wrap(script_text, body_font, text_area_width)
            raw_source_override = None

        # Resolve source image
        if raw_source_override:
            source = episode / raw_source_override
            if not source.exists():
                print(f"WARNING: explicit source {source} not found for {panel_id}, skipping")
                errors += 1
                continue
        else:
            source = find_raw_source(episode, panel_id)
            if source is None:
                print(f"WARNING: no raw source candidate found for {panel_id}, skipping")
                errors += 1
                continue

        out = render_panel(episode, panel_id, script_text, lines, source, dry_run=dry_run)
        if not dry_run:
            with Image.open(out) as img:
                size = img.size
            print(f"  {panel_id}: {out.name}  {size}  {out.stat().st_size // 1024} KB")

    if errors:
        print(f"\n{errors} panel(s) skipped due to missing sources.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render lettered caption panels for a pure comic episode.")
    parser.add_argument("episode", help="Path to episode directory, e.g. episodes/star-in-uniform-001")
    parser.add_argument("--panel", help="Only render this panel id, e.g. p003")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files")
    args = parser.parse_args()

    episode = Path(args.episode)
    if not episode.is_dir():
        sys.exit(f"Episode directory not found: {episode}")

    print(f"Rendering captions for {episode.name} ...")
    process_episode(episode, only_panel=args.panel, dry_run=args.dry_run)
    print("Done.")


if __name__ == "__main__":
    main()
