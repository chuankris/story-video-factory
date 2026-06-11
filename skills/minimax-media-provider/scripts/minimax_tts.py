#!/usr/bin/env python3
"""Batch MiniMax TTS (t2a_v2) for a script.json.

Usage:
    python minimax_tts.py --script script.json --outdir assets/audio \
        [--voice audiobook_male_1] [--model speech-2.8-hd] [--speed 1.0] \
        [--ids 3,7] [--force]

Env: MINIMAX_API_KEY, MINIMAX_GROUP_ID, optional MINIMAX_API_HOST.
Skips segments whose output file already exists unless --force.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

HOST = os.environ.get("MINIMAX_API_HOST", "https://api.minimaxi.chat")


def normalize_segments(data):
    """Accept segments / lines / scenes schemas (kept in sync with
    comic-video-composer's make_subtitles.normalize_segments)."""
    if isinstance(data, list):
        raw = data
    elif "segments" in data:
        raw = data["segments"]
    elif "lines" in data:
        raw = data["lines"]
    elif "scenes" in data:
        raw = []
        for scene in data["scenes"]:
            raw.extend(scene.get("narration_lines") or scene.get("lines") or [])
    else:
        sys.exit(f"unrecognized script schema; top-level keys: {list(data)}")
    segs = []
    for i, item in enumerate(raw, 1):
        if isinstance(item, str):
            segs.append({"id": i, "text": item})
            continue
        text = item.get("text") or item.get("line") or item.get("narration")
        if not text:
            sys.exit(f"segment {i} has no text field: {list(item)}")
        segs.append({"id": item.get("id", i), "text": text})
    return segs


def env(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f"missing env var {name}")
    return v


def tts(text, model, voice, speed):
    url = f"{HOST}/v1/t2a_v2?GroupId={env('MINIMAX_GROUP_ID')}"
    body = {
        "model": model,
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": voice, "speed": speed, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000,
                          "format": "mp3", "channel": 1},
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {env('MINIMAX_API_KEY')}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read())
    base = resp.get("base_resp", {})
    if base.get("status_code", 0) != 0:
        raise RuntimeError(f"API error {base.get('status_code')}: {base.get('status_msg')}")
    audio_hex = resp["data"]["audio"]
    return bytes.fromhex(audio_hex)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--model", default="speech-2.8-hd")
    ap.add_argument("--voice", default="audiobook_male_1")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--ids", default=None, help="comma-separated segment ids to (re)generate")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    segs = normalize_segments(json.loads(a.script.read_text(encoding="utf-8")))
    only = set(a.ids.split(",")) if a.ids else None
    a.outdir.mkdir(parents=True, exist_ok=True)

    done = skipped = failed = 0
    for seg in segs:
        sid = str(seg["id"])
        if only and sid not in only:
            continue
        out = a.outdir / f"{sid}.mp3"
        if out.exists() and not a.force:
            skipped += 1
            continue
        try:
            out.write_bytes(tts(seg["text"], a.model, a.voice, a.speed))
            done += 1
            print(f"ok  {sid}: {seg['text'][:20]}...")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {sid}: {e}", file=sys.stderr)
        time.sleep(0.5)  # be polite to rate limits

    print(f"generated={done} skipped={skipped} failed={failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
