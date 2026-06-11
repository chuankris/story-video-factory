#!/usr/bin/env python3
"""Smoke test for comic-video-composer.

Builds a fake 3-segment episode (ffmpeg-generated images + sine audio),
runs the full compose pipeline, and checks the output exists.
Also unit-checks the script-schema adapter (segments / lines / scenes).

Run from repo root:  python tests/smoke_compose.py
Requires: ffmpeg on PATH. No API keys needed.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "comic-video-composer" / "scripts"
EP = ROOT / "tests" / "fixture-episode"

SEGMENTS = [
    {"id": 1, "role": "narration",
     "text": "一个大活人，睡到半夜，床底下伸出一只手来。", "beat": "hook"},
    {"id": 2, "role": "narration",
     "text": "列位看官，这事就出在徽州程家。", "beat": "setup"},
    {"id": 3, "role": "narration",
     "text": "你道这只手，到底是人是鬼？", "beat": "close"},
]


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    return r


def check_adapter():
    sys.path.insert(0, str(SCRIPTS))
    import make_subtitles  # noqa: PLC0415

    variants = [
        {"segments": SEGMENTS},
        {"lines": [s["text"] for s in SEGMENTS]},
        {"lines": [{"id": s["id"], "text": s["text"]} for s in SEGMENTS]},
        {"scenes": [{"narration_lines": [SEGMENTS[0]["text"], SEGMENTS[1]["text"]]},
                    {"lines": [SEGMENTS[2]["text"]]}]},
    ]
    for v in variants:
        segs = make_subtitles.normalize_segments(v)
        assert len(segs) == 3, f"adapter returned {len(segs)} for {list(v)}"
        assert all(s["text"] and s["id"] for s in segs)
    print("adapter ok: segments / lines(str) / lines(dict) / scenes all normalize to 3 segments")

    # UTF-8 BOM tolerance: Notepad/PowerShell often write JSON with a BOM,
    # which plain json.loads(utf-8 text) rejects. Loaders must use utf-8-sig.
    bom_ep = ROOT / "tests" / "fixture-bom"
    if bom_ep.exists():
        shutil.rmtree(bom_ep)
    bom_ep.mkdir(parents=True)
    payload = json.dumps({"segments": SEGMENTS}, ensure_ascii=False).encode("utf-8")
    (bom_ep / "script.json").write_bytes(b"\xef\xbb\xbf" + payload)
    segs = make_subtitles.load_segments(bom_ep)
    assert len(segs) == 3 and segs[0]["text"].startswith("一个大活人")
    shutil.rmtree(bom_ep)
    print("bom ok: script.json with UTF-8 BOM loads correctly")


def build_fixture():
    if EP.exists():
        shutil.rmtree(EP)
    (EP / "assets" / "images").mkdir(parents=True)
    (EP / "assets" / "audio").mkdir(parents=True)
    (EP / "script.json").write_text(
        json.dumps({"episode": "测试", "segments": SEGMENTS}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    colors = ["0x334455", "0x553344", "0x445533"]
    freqs = [440, 550, 660]
    durs = [2.5, 2.0, 3.0]
    for i in range(3):
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={colors[i]}:s=1080x1440",
             "-frames:v", "1", EP / "assets" / "images" / f"{i + 1}.png"])
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency={freqs[i]}:duration={durs[i]}",
             "-c:a", "libmp3lame", EP / "assets" / "audio" / f"{i + 1}.mp3"])
    print("fixture built")


def main():
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")
    check_adapter()
    build_fixture()
    run([sys.executable, SCRIPTS / "compose.py", "--episode", EP])
    draft = EP / "output" / "draft.mp4"
    if not draft.exists() or draft.stat().st_size < 100_000:
        sys.exit(f"draft missing or suspiciously small: {draft}")
    print(f"\nSMOKE TEST PASSED -> {draft}")
    print("Expect: ~8s, 9:16, 3 color blocks with zoom/pan, subtitles, beeps.")


if __name__ == "__main__":
    main()
