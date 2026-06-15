"""Copy final panel images into the numbered Douyin carousel upload folder.

Usage:
    python skills/story-video-factory/scripts/build_publish_carousel.py <episode_dir>
    python skills/story-video-factory/scripts/build_publish_carousel.py <episode_dir> --force
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from PIL import Image


MIN_FILE_BYTES = 500 * 1024  # 500 KB


def load_panel_order(episode: Path) -> list[str]:
    raw = (episode / "script.json").read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    segments = data.get("segments", data if isinstance(data, list) else [])
    return [seg["id"] for seg in segments]


def check_ratio(path: Path) -> tuple[bool, tuple[int, int]]:
    with Image.open(path) as img:
        w, h = img.size
    return (w * 16 == h * 9, (w, h))


def build_carousel(episode: Path, force: bool = False) -> None:
    panel_ids = load_panel_order(episode)
    images_dir = episode / "assets" / "images"
    carousel_dir = episode / "output" / "publish" / "carousel"

    missing = [pid for pid in panel_ids if not (images_dir / f"{pid}.png").exists()]
    if missing:
        sys.exit(f"ERROR: missing final panels: {missing}\nRun render_lettered_panels.py first.")

    carousel_dir.mkdir(parents=True, exist_ok=True)

    errors = 0
    for seq, panel_id in enumerate(panel_ids, start=1):
        src = images_dir / f"{panel_id}.png"
        dst = carousel_dir / f"{seq:02d}-{panel_id}.png"

        if dst.exists() and not force:
            print(f"  SKIP {dst.name} (already exists; use --force to overwrite)")
            continue

        is_916, (w, h) = check_ratio(src)
        size_bytes = src.stat().st_size
        warnings = []
        if not is_916:
            warnings.append(f"NOT 9:16 ({w}x{h})")
        if size_bytes < MIN_FILE_BYTES:
            warnings.append(f"small file ({size_bytes // 1024} KB < 500 KB)")

        shutil.copy2(src, dst)
        status = "WARN" if warnings else "ok  "
        warn_str = " | ".join(warnings)
        print(f"  {status} {seq:02d} {panel_id}  {w}x{h}  {size_bytes // 1024} KB  {warn_str}")
        if warnings:
            errors += 1

    print(f"\nCarousel ready: {carousel_dir}")
    if errors:
        print(f"{errors} panel(s) had warnings - review before uploading.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Douyin carousel upload folder from final panels.")
    parser.add_argument("episode", help="Path to episode directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing carousel files")
    args = parser.parse_args()

    episode = Path(args.episode)
    if not episode.is_dir():
        sys.exit(f"Episode directory not found: {episode}")

    build_carousel(episode, force=args.force)


if __name__ == "__main__":
    main()
