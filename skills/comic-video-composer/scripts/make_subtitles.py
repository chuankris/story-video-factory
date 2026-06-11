#!/usr/bin/env python3
"""Generate an .ass subtitle file from script.json + per-segment audio durations.

Usage:
    python make_subtitles.py --episode <episode-dir> [--out subtitles.ass]

Expects:
    <episode-dir>/script.json            segments: [{id, text, ...}]
    <episode-dir>/assets/audio/<id>.mp3  (or .wav) one file per segment
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

PAD = 0.3  # seconds of padding after each segment's audio
MAX_LINE = 14  # CJK chars per subtitle line

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Narration,Noto Sans CJK SC,72,&H00FFFFFF,&H000000FF,&H00000000,&H7F000000,1,0,0,0,100,100,0,0,1,4,2,2,60,60,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def audio_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def find_audio(audio_dir: Path, seg_id) -> Path:
    for ext in (".mp3", ".wav", ".m4a", ".flac"):
        p = audio_dir / f"{seg_id}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"no audio for segment {seg_id} in {audio_dir}")


def wrap(text: str) -> str:
    text = text.strip()
    if len(text) <= MAX_LINE:
        return text
    mid = (len(text) + 1) // 2
    return text[:mid] + r"\N" + text[mid:]


def ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build(episode: Path, out: Path) -> None:
    script = json.loads((episode / "script.json").read_text(encoding="utf-8"))
    audio_dir = episode / "assets" / "audio"
    events, t = [], 0.0
    for seg in script["segments"]:
        dur = audio_duration(find_audio(audio_dir, seg["id"])) + PAD
        events.append(
            f"Dialogue: 0,{ts(t)},{ts(t + dur - 0.1)},Narration,,0,0,0,,{wrap(seg['text'])}")
        t += dur
    out.write_text(ASS_HEADER + "\n".join(events) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(events)} events, total {t:.1f}s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    build(a.episode, a.out or a.episode / "output" / "subtitles.ass")
