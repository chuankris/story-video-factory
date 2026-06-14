"""Generate a QC report skeleton for a pure comic episode.

Usage:
    python skills/story-video-factory/scripts/generate_qc_report.py <episode_dir>
    python skills/story-video-factory/scripts/generate_qc_report.py <episode_dir> --force
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_raw_source(episode: Path, panel_id: str) -> str:
    candidates = sorted((episode / "assets" / "images-raw").glob(f"{panel_id}_*.png"))
    return str(candidates[0].relative_to(episode)) if candidates else "unknown"


def panel_section(episode: Path, panel_id: str, provider: str) -> str:
    final = episode / "assets" / "images" / f"{panel_id}.png"
    if not final.exists():
        return f"## {panel_id}\n\nFile: MISSING\n\n"

    with Image.open(final) as img:
        w, h = img.size
    size_kb = final.stat().st_size // 1024
    is_916 = "pass" if w * 16 == h * 9 else "FAIL"
    res_pass = "pass" if h >= 1920 else "FAIL"
    source = find_raw_source(episode, panel_id)

    return f"""## {panel_id}

File: `assets/images/{panel_id}.png`
Source: `{source}`
Provider: `{provider}`
Size: `{w}x{h}`, {size_kb} KB

Checks:
- resolution: {res_pass}
- 9:16 ratio: {is_916}
- story fit: # TODO: human review
- style consistency: # TODO: human review
- character consistency: # TODO: human review
- unwanted text/logo/watermark: # TODO: human review
- caption readability: # TODO: human review

Decision: # TODO: accept / rerun / manual-intake
Reason:

"""


def carousel_section(episode: Path, panel_ids: list[str]) -> str:
    carousel_dir = episode / "output" / "publish" / "carousel"
    carousel_files = sorted(carousel_dir.glob("*.png")) if carousel_dir.exists() else []
    carousel_count = len(carousel_files)

    return f"""## Carousel-Level QC

Episode id: `{episode.name}`
Total panels: {len(panel_ids)}
Carousel files found: {carousel_count}
Caption source: `script.json`

Checks:
- total panel count: {"pass" if carousel_count == len(panel_ids) else f"FAIL ({carousel_count} found, {len(panel_ids)} expected)"}
- first image works as cover: # TODO: human review
- story understandable without narration: # TODO: human review
- captions progress in image order: # TODO: human review
- no duplicate adjacent panels: # TODO: human review
- final panel provides payoff: # TODO: human review
- all panels 9:16: (see per-panel above)
- important details visible on phone: # TODO: human review
- publish package created: {"pass" if (episode / "output" / "publish" / "pack.md").exists() else "pending"}

Carousel decision: # TODO: ready / needs-reorder / needs-rerun
"""


def generate_report(episode: Path, force: bool = False) -> None:
    meta = load_json(episode / "episode-meta.json")
    script_data = load_json(episode / "script.json")
    segments = script_data.get("segments", script_data if isinstance(script_data, list) else [])
    panel_ids = [seg["id"] for seg in segments]

    provider = meta.get("provider_plan", {}).get("production_panels", "unknown")
    title = meta.get("title", episode.name)
    mode = meta.get("production_mode", "pure_comic")

    out_path = episode / "output" / "qc-report.generated.md"
    final_path = episode / "output" / "qc-report.md"

    if final_path.exists() and not force:
        target = out_path
        print(f"NOTE: qc-report.md already exists. Writing to {out_path.name} (use --force to overwrite qc-report.md).")
    else:
        target = final_path if force else out_path

    lines = [
        f"# QC Report: {title}\n\n",
        f"Episode id: `{episode.name}`  \n",
        f"Mode: `{mode}`  \n",
        f"Provider: `{provider}`  \n",
        f"Caption source: `script.json`  \n",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  \n",
        "\n## Summary\n\n# TODO: fill in after per-panel review\n\n",
    ]

    for panel_id in panel_ids:
        lines.append(panel_section(episode, panel_id, provider))

    lines.append(carousel_section(episode, panel_ids))

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(lines), encoding="utf-8")
    print(f"QC report written: {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate QC report skeleton for a pure comic episode.")
    parser.add_argument("episode", help="Path to episode directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing qc-report.md")
    args = parser.parse_args()

    episode = Path(args.episode)
    if not episode.is_dir():
        sys.exit(f"Episode directory not found: {episode}")

    generate_report(episode, force=args.force)


if __name__ == "__main__":
    main()
