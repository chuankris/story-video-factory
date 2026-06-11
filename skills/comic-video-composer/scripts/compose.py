#!/usr/bin/env python3
"""Compose comic panels + per-segment TTS audio into a 9:16 draft video.

Usage:
    python compose.py --episode <episode-dir> [--music bgm.mp3] [--fps 30]

Expects inside <episode-dir>:
    script.json                 {"segments": [{"id": 1, "text": "...", "beat": "hook"}, ...]}
                                (legacy {"lines": [...]} / {"scenes": [...]} also accepted)
    assets/images/<id>.png|jpg  one panel per segment (image_map.json may remap)
    assets/audio/<id>.mp3|wav   one narration clip per segment
Optional:
    image_map.json              {"<segment-id>": "<image filename>"} to reuse panels

Produces:
    output/segments/<id>.mp4    per-segment clips
    output/subtitles.ass
    output/draft.mp4
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import make_subtitles  # sibling module: duration probing + .ass generation

W, H = 1080, 1920
PAD = make_subtitles.PAD

MOTIONS = ["zoom_in", "zoom_out", "pan_left", "pan_right"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r


def find_image(images: Path, seg_id, image_map) -> Path:
    name = image_map.get(str(seg_id))
    if name:
        p = images / name
        if p.exists():
            return p
        sys.exit(f"image_map points to missing file: {p}")
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = images / f"{seg_id}{ext}"
        if p.exists():
            return p
    sys.exit(f"missing image for segment {seg_id} in {images}")


def motion_filter(kind: str, dur: float, fps: int, strong: bool) -> str:
    """Ken Burns via zoompan. Pre-scale 2x to reduce jitter."""
    frames = max(int(dur * fps), 1)
    zmax = 1.15 if strong else 1.08
    pre = f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
    if kind == "zoom_in":
        z = f"min(1+({zmax}-1)*on/{frames},{zmax})"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif kind == "zoom_out":
        z = f"max({zmax}-({zmax}-1)*on/{frames},1)"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif kind == "pan_left":
        z = f"{zmax}"
        x, y = f"(iw-iw/zoom)*(1-on/{frames})", "ih/2-(ih/zoom/2)"
    else:  # pan_right
        z = f"{zmax}"
        x, y = f"(iw-iw/zoom)*on/{frames}", "ih/2-(ih/zoom/2)"
    return (pre + f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={fps},"
            f"format=yuv420p")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True, type=Path)
    ap.add_argument("--music", type=Path, default=None)
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    ep = a.episode

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("ffmpeg/ffprobe not found on PATH")

    segments = make_subtitles.load_segments(ep)
    images, audio = ep / "assets" / "images", ep / "assets" / "audio"
    image_map = {}
    if (ep / "image_map.json").exists():
        image_map = json.loads((ep / "image_map.json").read_text(encoding="utf-8-sig"))

    out = ep / "output"
    segdir = out / "segments"
    segdir.mkdir(parents=True, exist_ok=True)

    # 1) per-segment clips
    clips = []
    for i, seg in enumerate(segments):
        sid = seg["id"]
        img = find_image(images, sid, image_map)
        aud = make_subtitles.find_audio(audio, sid)
        dur = make_subtitles.audio_duration(aud) + PAD
        strong = seg.get("beat") in ("hook", "reveal")
        vf = motion_filter(MOTIONS[i % len(MOTIONS)], dur, a.fps, strong)
        clip = segdir / f"{sid}.mp4"
        run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-i", aud,
             "-t", f"{dur:.3f}", "-vf", vf,
             "-c:v", "libx264", "-preset", "medium", "-crf", "19",
             "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
             "-shortest", clip])
        clips.append(clip)
        print(f"segment {sid}: {dur:.2f}s")

    # 2) subtitles
    ass = out / "subtitles.ass"
    make_subtitles.build(ep, ass)

    # 3) concat
    lst = out / "concat.txt"
    lst.write_text("".join(f"file '{c.resolve().as_posix()}'\n" for c in clips),
                   encoding="utf-8")
    merged = out / "merged.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", merged])

    # 4) burn subtitles (+ optional ducked music)
    draft = out / "draft.mp4"
    ass_f = ass.resolve().as_posix().replace(":", r"\:")
    if a.music:
        run(["ffmpeg", "-y", "-i", merged, "-stream_loop", "-1", "-i", a.music,
             "-filter_complex",
             f"[0:v]subtitles='{ass_f}'[v];"
             f"[1:a]volume=-18dB[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
             "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-preset", "medium", "-crf", "19",
             "-c:a", "aac", "-b:a", "192k", draft])
    else:
        run(["ffmpeg", "-y", "-i", merged, "-vf", f"subtitles='{ass_f}'",
             "-c:v", "libx264", "-preset", "medium", "-crf", "19",
             "-c:a", "copy", draft])

    print(f"done: {draft}")


if __name__ == "__main__":
    main()
