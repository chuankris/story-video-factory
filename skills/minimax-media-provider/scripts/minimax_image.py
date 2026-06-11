#!/usr/bin/env python3
"""MiniMax image generation (image-01): text-to-image with optional subject reference.

Usage:
    # single prompt
    python minimax_image.py --prompt "..." --outdir assets/images-raw \
        [--n 4] [--aspect 3:4] [--subject character_ref.png]

    # batch from prompts.json: [{"id": "1", "prompt": "...", "count": 1}, ...]
    python minimax_image.py --prompts prompts.json --outdir assets/images-raw \
        [--aspect 3:4] [--subject character_ref.png] [--force]

Env: MINIMAX_API_KEY, optional MINIMAX_API_HOST.
Batch mode skips ids whose output already exists unless --force.
Subject reference keeps character faces consistent across panels.
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.request
from pathlib import Path

HOST = os.environ.get("MINIMAX_API_HOST", "https://api.minimaxi.com")


def env(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f"missing env var {name}")
    return v


def data_url(path: str) -> str:
    mime = mimetypes.guess_type(path)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


def generate(prompt, n, aspect, subject):
    body = {
        "model": "image-01",
        "prompt": prompt,
        "aspect_ratio": aspect,
        "n": n,
        "response_format": "base64",
    }
    if subject:
        body["subject_reference"] = [{"type": "character", "image_file": data_url(subject)}]
    req = urllib.request.Request(
        f"{HOST}/v1/image_generation",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {env('MINIMAX_API_KEY')}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read())
    base_resp = resp.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        raise RuntimeError(f"API error {base_resp.get('status_code')}: {base_resp.get('status_msg')}")
    data = resp.get("data", {})
    images = data.get("image_base64") or data.get("images") or []
    if not images:
        raise RuntimeError(f"no images in response: {list(resp)}")
    return [base64.b64decode(b64) for b64 in images]


def save_set(blobs, outdir: Path, stem: str):
    outdir.mkdir(parents=True, exist_ok=True)
    names = []
    for i, blob in enumerate(blobs):
        p = outdir / f"{stem}_{chr(97 + i)}.png"
        p.write_bytes(blob)
        names.append(p.name)
    return names


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompts", type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--aspect", default="3:4")
    ap.add_argument("--subject", default=None, help="character reference image")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if a.prompt:
        names = save_set(generate(a.prompt, a.n, a.aspect, a.subject), a.outdir, "img")
        print(f"ok: {names}")
        return

    items = json.loads(a.prompts.read_text(encoding="utf-8-sig"))
    done = skipped = failed = 0
    for item in items:
        sid = str(item["id"])
        if not a.force and list(a.outdir.glob(f"{sid}_*.png")):
            skipped += 1
            continue
        try:
            names = save_set(
                generate(item["prompt"], item.get("count", 1), a.aspect, a.subject),
                a.outdir, sid)
            done += 1
            print(f"ok  {sid}: {names}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {sid}: {e}", file=sys.stderr)
        time.sleep(6)  # ~10 RPM limit
    print(f"generated={done} skipped={skipped} failed={failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
