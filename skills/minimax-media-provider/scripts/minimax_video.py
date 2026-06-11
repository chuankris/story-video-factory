#!/usr/bin/env python3
"""MiniMax (Hailuo) async video generation: submit and poll tasks.

Usage:
    python minimax_video.py submit --prompt "..." [--image first.png] \
        [--model MiniMax-Hailuo-02] [--duration 6] [--resolution 1080P] \
        [--tasks video-tasks.json] [--outdir assets/video]
    python minimax_video.py poll [--tasks video-tasks.json] [--outdir assets/video]

Env: MINIMAX_API_KEY, optional MINIMAX_GROUP_ID (file retrieval), MINIMAX_API_HOST.
Tasks are tracked in a local JSON file so polling survives restarts.
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

HOST = os.environ.get("MINIMAX_API_HOST", "https://api.minimaxi.chat")


def env(name, required=True):
    v = os.environ.get(name)
    if required and not v:
        sys.exit(f"missing env var {name}")
    return v


def api(method, path, body=None):
    req = urllib.request.Request(
        f"{HOST}{path}",
        data=json.dumps(body).encode() if body else None,
        method=method,
        headers={"Authorization": f"Bearer {env('MINIMAX_API_KEY')}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read())
    base_resp = resp.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        raise RuntimeError(f"API error {base_resp.get('status_code')}: {base_resp.get('status_msg')}")
    return resp


def load_tasks(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save_tasks(p: Path, tasks):
    p.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def submit(a):
    body = {"model": a.model, "prompt": a.prompt,
            "duration": a.duration, "resolution": a.resolution}
    if a.image:
        mime = mimetypes.guess_type(a.image)[0] or "image/png"
        b64 = base64.b64encode(Path(a.image).read_bytes()).decode()
        body["first_frame_image"] = f"data:{mime};base64,{b64}"
    resp = api("POST", "/v1/video_generation", body)
    task_id = resp["task_id"]
    tasks = load_tasks(a.tasks)
    tasks.append({"task_id": task_id, "prompt": a.prompt[:80],
                  "submitted": time.strftime("%Y-%m-%d %H:%M:%S"),
                  "status": "pending"})
    save_tasks(a.tasks, tasks)
    print(f"submitted task {task_id}")


def download(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=600) as r:
        dest.write_bytes(r.read())


def poll(a):
    tasks = load_tasks(a.tasks)
    pending = [t for t in tasks if t["status"] == "pending"]
    if not pending:
        print("no pending tasks")
        return
    group = env("MINIMAX_GROUP_ID", required=False)
    for t in pending:
        resp = api("GET", f"/v1/query/video_generation?task_id={t['task_id']}")
        status = resp.get("status")
        print(f"{t['task_id']}: {status}")
        if status == "Success":
            file_id = resp["file_id"]
            q = f"/v1/files/retrieve?file_id={file_id}"
            if group:
                q += f"&GroupId={group}"
            url = api("GET", q)["file"]["download_url"]
            dest = a.outdir / f"{t['task_id']}.mp4"
            download(url, dest)
            t["status"] = "done"
            t["file"] = str(dest)
            print(f"  downloaded -> {dest}")
        elif status == "Fail":
            t["status"] = "failed"
            t["reason"] = resp.get("base_resp", {}).get("status_msg", "unknown")
    save_tasks(a.tasks, tasks)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("submit")
    s.add_argument("--prompt", required=True)
    s.add_argument("--image", default=None)
    s.add_argument("--model", default="MiniMax-Hailuo-02")
    s.add_argument("--duration", type=int, default=6)
    s.add_argument("--resolution", default="1080P")
    p = sub.add_parser("poll")
    for x in (s, p):
        x.add_argument("--tasks", type=Path, default=Path("video-tasks.json"))
        x.add_argument("--outdir", type=Path, default=Path("assets/video"))
    a = ap.parse_args()
    submit(a) if a.cmd == "submit" else poll(a)


if __name__ == "__main__":
    main()
