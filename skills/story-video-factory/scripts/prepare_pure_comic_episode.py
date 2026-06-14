"""Orchestrate pure-comic post-production: render → carousel → QC → publish pack.

Usage:
    python skills/story-video-factory/scripts/prepare_pure_comic_episode.py <episode_dir>
    python skills/story-video-factory/scripts/prepare_pure_comic_episode.py <episode_dir> --skip-render --force
    python skills/story-video-factory/scripts/prepare_pure_comic_episode.py <episode_dir> --contact-sheet
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).parent


def _import_script(name: str):
    script_path = _SCRIPTS / f"{name}.py"
    if not script_path.exists():
        sys.exit(f"ERROR: required script not found: {script_path}")
    spec = importlib.util.spec_from_file_location(name, script_path)
    if spec is None or spec.loader is None:
        sys.exit(f"ERROR: could not load script: {script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_contact_sheet(episode: Path) -> None:
    from PIL import Image

    script_data = json.loads((episode / "script.json").read_text(encoding="utf-8-sig"))
    segments = script_data.get("segments", [])
    panel_ids = [seg["id"] for seg in segments]

    images_dir = episode / "assets" / "images"
    thumbs = []
    for pid in panel_ids:
        src = images_dir / f"{pid}.png"
        if src.exists():
            with Image.open(src) as raw:
                img = raw.convert("RGB")
            img.thumbnail((216, 384), Image.Resampling.LANCZOS)
            thumbs.append(img)

    if not thumbs:
        print("WARNING: no final panels found for contact sheet")
        return

    cols = 5
    rows = (len(thumbs) + cols - 1) // cols
    tw, th = 216, 384
    sheet = Image.new("RGB", (cols * tw, rows * th), (30, 30, 30))
    for i, thumb in enumerate(thumbs):
        r, c = divmod(i, cols)
        sheet.paste(thumb, (c * tw, r * th))

    out = episode / "output" / f"{episode.name}_sheet.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=88)
    print(f"Contact sheet: {out}  {sheet.size}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full pure-comic post-production pipeline for an episode."
    )
    parser.add_argument("episode", help="Path to episode directory")
    parser.add_argument("--skip-render", action="store_true", help="Skip caption rendering")
    parser.add_argument("--skip-carousel", action="store_true", help="Skip carousel packaging")
    parser.add_argument("--skip-qc", action="store_true", help="Skip QC report generation")
    parser.add_argument("--skip-pack", action="store_true", help="Skip publish pack generation")
    parser.add_argument("--contact-sheet", action="store_true", help="Also generate contact sheet")
    parser.add_argument("--force", action="store_true", help="Pass --force to all sub-steps")
    args = parser.parse_args()

    episode = Path(args.episode)
    if not episode.is_dir():
        sys.exit(f"Episode directory not found: {episode}")

    print(f"\n{'='*60}")
    print(f"Pure Comic Episode Packaging: {episode.name}")
    print(f"{'='*60}\n")

    if not args.skip_render:
        print("── Step 1: Render caption panels ──")
        renderer = _import_script("render_lettered_panels")
        renderer.process_episode(episode)
        print()

    if not args.skip_carousel:
        print("── Step 2: Build publish carousel ──")
        carousel = _import_script("build_publish_carousel")
        carousel.build_carousel(episode, force=args.force)
        print()

    if not args.skip_qc:
        print("── Step 3: Generate QC report ──")
        qc = _import_script("generate_qc_report")
        qc.generate_report(episode, force=args.force)
        print()

    if not args.skip_pack:
        print("── Step 4: Generate publish pack ──")
        pack = _import_script("generate_publish_pack")
        pack.generate_pack(episode, force=args.force)
        print()

    if args.contact_sheet:
        print("── Step 5: Build contact sheet ──")
        build_contact_sheet(episode)
        print()

    print(f"\n{'='*60}")
    print("Done. Next steps:")
    print("  1. Review output/qc-report.generated.md — fill in subjective checks.")
    print("  2. Edit output/publish/pack.generated.md — customise titles and copy.")
    print("  3. Upload output/publish/carousel/ to Douyin in numeric order.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
