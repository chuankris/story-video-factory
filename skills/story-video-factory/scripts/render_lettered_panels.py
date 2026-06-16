"""Batch caption renderer for pure comic episodes.

Usage:
    python skills/story-video-factory/scripts/render_lettered_panels.py <episode_dir>
    python skills/story-video-factory/scripts/render_lettered_panels.py <episode_dir> --style douyin-msyh-top
    python skills/story-video-factory/scripts/render_lettered_panels.py <episode_dir> --panel p003
    python skills/story-video-factory/scripts/render_lettered_panels.py <episode_dir> --dry-run
    python skills/story-video-factory/scripts/render_lettered_panels.py <episode_dir> --force-render

Source resolution (per panel, in priority order):
  1. caption-layout.json "source" field for that panel
  2. selected-candidates.json entry for that panel
  3. If neither: skip if assets/images/<id>.png already exists (safe default)
     Use --force-render to overwrite, but a source must still be configured.

Create selected-candidates.json in the episode dir to track approved sources:
  {
    "p001": "assets/images-raw/p001_002.png",
    "p002": "assets/images-raw/p002_001.png"
  }
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

MSYH_BOLD_PATHS = [
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
]

STYLES = ("bottom-card", "douyin-msyh-top")


def make_font(size: int, paths: list[str] | None = None) -> ImageFont.FreeTypeFont:
    for path in paths or FONT_PATHS:
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


def fit_douyin_top_font(lines: list[str]) -> tuple[ImageFont.FreeTypeFont, int]:
    """Pick a Microsoft YaHei font size that keeps text in the top safe card."""
    for size in (52, 49, 46, 43, 40):
        font = make_font(size, MSYH_BOLD_PATHS)
        if all(font.getlength(line) <= 790 for line in lines):
            line_gap = int(size * 1.34)
            card_h = 72 + len(lines) * line_gap
            if card_h <= 670:
                return font, line_gap
    size = 38
    return make_font(size, MSYH_BOLD_PATHS), int(size * 1.34)


def fit_auto_douyin_top_lines(text: str) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    """Auto-wrap fallback for episodes without manual caption-layout lines."""
    for size in (52, 49, 46, 43, 40):
        font = make_font(size, MSYH_BOLD_PATHS)
        lines = auto_wrap(text, font, 770)
        line_gap = int(size * 1.34)
        card_h = 72 + len(lines) * line_gap
        if len(lines) <= 7 and card_h <= 670:
            return font, lines, line_gap
    font = make_font(38, MSYH_BOLD_PATHS)
    return font, auto_wrap(text, font, 780), int(38 * 1.34)


def normalize_to_canvas(source: Path) -> Image.Image:
    img = Image.open(source).convert("RGB")
    scale = max(W / img.width, H / img.height)
    img = img.resize(
        (int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS
    )
    left = (img.width - W) // 2
    top = (img.height - H) // 2
    return img.crop((left, top, left + W, top + H)).convert("RGBA")


def render_bottom_card(base: Image.Image, lines: list[str], page_label: str) -> Image.Image:
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
    return base


def render_douyin_msyh_top(
    base: Image.Image,
    script_text: str,
    lines: list[str],
    page_label: str,
) -> Image.Image:
    """Render readable Microsoft YaHei captions in the upper safe zone.

    This style avoids the bottom 22% Douyin UI zone and keeps key text away
    from the right-side action buttons. It is intentionally sourced from
    UTF-8 files (`script.json` / `caption-layout.json`), not shell literals.
    """
    if lines:
        font, line_gap = fit_douyin_top_font(lines)
    else:
        font, lines, line_gap = fit_auto_douyin_top_lines(script_text)
    small = make_font(24)

    text_x = 86
    text_y = 154
    card_w = 825
    card_h = 72 + len(lines) * line_gap
    card = (52, 128, 52 + card_w, 128 + card_h)

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (card[0] + 6, card[1] + 10, card[2] + 6, card[3] + 10),
        radius=34,
        fill=(75, 55, 35, 38),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    base.alpha_composite(shadow)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(card, radius=34, fill=(255, 248, 229, 120))
    base.alpha_composite(overlay)

    draw = ImageDraw.Draw(base)
    brush_colors = [(205, 145, 132, 116), (154, 179, 186, 105)]
    for i, line in enumerate(lines):
        ly = text_y + i * line_gap
        bbox = draw.textbbox((text_x, ly), line, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        strip_y = ly + th // 2 - 9
        draw.rounded_rectangle(
            (text_x - 14, strip_y, text_x + tw + 14, strip_y + 34),
            radius=13,
            fill=brush_colors[i % 2],
        )
        draw.text((text_x, ly), line, fill=(35, 30, 24, 255), font=font)

    draw.text((card[2] - 68, card[3] - 42), page_label, fill=(110, 96, 78, 150), font=small)
    return base


def load_selected_candidates(episode: Path) -> dict[str, str]:
    """Load selected-candidates.json as {panel_id: relative_source_path}."""
    path = episode / "selected-candidates.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return {k: v for k, v in data.items() if isinstance(v, str)}
    except Exception as e:
        print(f"WARNING: could not read selected-candidates.json: {e}")
        return {}


def render_panel(
    episode: Path,
    panel_id: str,
    script_text: str,
    lines: list[str],
    source: Path,
    dry_run: bool = False,
    style: str = "bottom-card",
) -> Path:
    if style not in STYLES:
        sys.exit(f"ERROR: unknown render style '{style}'. Choose one of: {', '.join(STYLES)}")

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
        print(f"[dry-run] {panel_id}: {source} -> {out}  style={style}  lines={lines}")
        return out

    base = normalize_to_canvas(source)
    if style == "douyin-msyh-top":
        base = render_douyin_msyh_top(base, script_text, lines, page_label)
    else:
        base = render_bottom_card(base, lines, page_label)

    out.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out)
    return out


def process_episode(
    episode: Path,
    only_panel: str | None = None,
    dry_run: bool = False,
    force_render: bool = False,
    style: str = "bottom-card",
) -> None:
    if style not in STYLES:
        sys.exit(f"ERROR: unknown render style '{style}'. Choose one of: {', '.join(STYLES)}")

    scripts = load_script(episode)
    layout = load_caption_layout(episode)
    selected = load_selected_candidates(episode)

    if style == "douyin-msyh-top":
        body_font = make_font(52, MSYH_BOLD_PATHS)
        text_area_width = 770
    else:
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

        # Resolve lines and caption-layout source override
        if panel_id in layout:
            entry = layout[panel_id]
            lines = entry["lines"]
            caption_source = entry["source"]
        else:
            lines = auto_wrap(script_text, body_font, text_area_width)
            caption_source = None

        # Source resolution priority:
        # 1. caption-layout.json "source" field
        # 2. selected-candidates.json entry
        # 3. No source: protect existing final (skip) unless --force-render, but still
        #    cannot render without a source; warn and skip either way.
        if caption_source:
            source = episode / caption_source
            if not source.exists():
                print(f"  WARNING: caption-layout source {source} not found for {panel_id}, skipping")
                errors += 1
                continue
        elif panel_id in selected:
            source = episode / selected[panel_id]
            if not source.exists():
                print(f"  WARNING: selected-candidates source {source} not found for {panel_id}, skipping")
                errors += 1
                continue
        else:
            # No source configured; protect the existing final image
            final = episode / "assets" / "images" / f"{panel_id}.png"
            if final.exists():
                print(f"  SKIP {panel_id}: final exists and no source configured"
                      " (add to selected-candidates.json or caption-layout.json source field)")
            else:
                print(f"  WARNING: {panel_id} has no source configured and no final image"
                      " - add to selected-candidates.json")
                errors += 1
            continue

        # Protect existing final unless --force-render
        final = episode / "assets" / "images" / f"{panel_id}.png"
        if final.exists() and not force_render:
            print(f"  SKIP {panel_id}: final already exists (use --force-render to overwrite)")
            continue

        out = render_panel(
            episode,
            panel_id,
            script_text,
            lines,
            source,
            dry_run=dry_run,
            style=style,
        )
        if not dry_run:
            with Image.open(out) as img:
                size = img.size
            print(
                f"  {panel_id}: {out.name}  {size}  {out.stat().st_size // 1024} KB"
                f"  style={style}  <- {source.name}"
            )

    if errors:
        print(f"\n{errors} panel(s) skipped due to missing or invalid sources.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render lettered caption panels for a pure comic episode.")
    parser.add_argument("episode", help="Path to episode directory, e.g. episodes/star-in-uniform-001")
    parser.add_argument("--panel", help="Only render this panel id, e.g. p003")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files")
    parser.add_argument(
        "--style",
        choices=STYLES,
        default="bottom-card",
        help="Caption render style. Use douyin-msyh-top for top safe-zone Microsoft YaHei captions.",
    )
    parser.add_argument(
        "--force-render",
        action="store_true",
        help="Overwrite existing final images (requires source to be configured)",
    )
    args = parser.parse_args()

    episode = Path(args.episode)
    if not episode.is_dir():
        sys.exit(f"Episode directory not found: {episode}")

    print(f"Rendering captions for {episode.name} ...")
    process_episode(
        episode,
        only_panel=args.panel,
        dry_run=args.dry_run,
        force_render=args.force_render,
        style=args.style,
    )
    print("Done.")


if __name__ == "__main__":
    main()
