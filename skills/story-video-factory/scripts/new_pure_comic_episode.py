"""Create a new pure-comic episode scaffold.

Usage:
    python skills/story-video-factory/scripts/new_pure_comic_episode.py episodes/my-story-001 --title "故事标题"
    python skills/story-video-factory/scripts/new_pure_comic_episode.py episodes/my-story-001 --title "故事标题" --panel-count 11 --era "2006 China" --theme "亲情"
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
TEMPLATE_DIR = REPO_ROOT / "references" / "templates" / "pure-comic-episode"


def episode_id_from_path(episode: Path) -> str:
    return episode.name


def write_json(path: Path, data: object) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def create_episode(
    episode: Path,
    *,
    title: str,
    panel_count: int = 10,
    era: str = "",
    theme: str = "",
    force: bool = False,
) -> Path:
    episode = episode.resolve()
    if episode.exists():
        if not force:
            raise SystemExit(f"Episode already exists: {episode}. Use --force to recreate it.")
        shutil.rmtree(episode)

    if not TEMPLATE_DIR.exists():
        raise SystemExit(f"Template directory not found: {TEMPLATE_DIR}")

    shutil.copytree(TEMPLATE_DIR, episode)

    for rel in (
        "assets/refs",
        "assets/images-raw",
        "assets/images",
        "assets/audio",
        "assets/video",
        "output/publish",
    ):
        (episode / rel).mkdir(parents=True, exist_ok=True)

    meta = {
        "episode_id": episode_id_from_path(episode),
        "title": title,
        "production_mode": "pure_comic",
        "draft_mode": False,
        "target_panel_count": panel_count,
        "era": era,
        "theme": theme,
        "provider_plan": {
            "style_anchor": "gpt-image",
            "production_panels": "gpt-image",
            "caption_style": "douyin-msyh-top",
            "notes": "New scaffold. Fill outline/script/storyboard/visual bible before spending provider quota.",
        },
        "jimeng_budget": {"max_prompts": 0, "candidates_per_panel": 0},
        "gpt_image_budget": {"max_images": panel_count + 3},
        "minimax_budget": {"tts": False, "video": False, "image_side_tests": 0},
        "review_gates": {
            "outline": "pending",
            "comic_script": "pending",
            "visual_bible": "pending",
            "final_assets": "pending",
        },
    }
    write_json(episode / "episode-meta.json", meta)
    write_json(episode / "selected-candidates.json", {})
    write_json(episode / "prompts-jimeng.json", [])

    return episode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a pure-comic episode scaffold.")
    parser.add_argument("episode", type=Path, help="Episode directory, e.g. episodes/my-story-001")
    parser.add_argument("--title", required=True, help="Human-readable episode title")
    parser.add_argument("--panel-count", type=int, default=10, help="Target story panel count")
    parser.add_argument("--era", default="", help="Optional era or setting, e.g. '2006 China'")
    parser.add_argument("--theme", default="", help="Optional theme note")
    parser.add_argument("--force", action="store_true", help="Recreate the episode if it already exists")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    episode = create_episode(
        args.episode,
        title=args.title,
        panel_count=args.panel_count,
        era=args.era,
        theme=args.theme,
        force=args.force,
    )
    print(f"Created pure-comic episode: {episode}")
    print("Next: fill outline.md, script.json, storyboard.json, style-profile.md, and visual-bible.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
