#!/usr/bin/env python3
"""Playwright automation for Jimeng (即梦) image/video generation.

Usage:
    python jimeng_run.py login    --profile .jimeng-profile
    python jimeng_run.py generate --profile .jimeng-profile \
        --prompts prompts.json --outdir assets/images-raw \
        [--video] [--state mystate.json] [--headless]
    python jimeng_run.py resume   --profile .jimeng-profile \
        --prompts prompts.json --outdir assets/images-raw [--video] [--state ...]

prompts.json: [{"id": "1", "prompt": "...", "count": 1}, ...]
State: defaults to <prompts-stem>.jimeng-state.json NEXT TO the prompts file
(per-batch, so different tests never pollute each other). Entries:
    {"<id>": {"status": "pending|submitted|confirmed|downloaded|failed",
              "workspace_url": "...", "files": [...], "error": "..."}}
`resume` reopens saved workspace URLs and downloads results that finished
after a timeout — Jimeng video can take a while.

Selectors: selectors.json next to this script — edit THAT file when the UI changes.
Requires: pip install playwright && playwright install chromium
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
SEL = json.loads((HERE / "selectors.json").read_text(encoding="utf-8-sig"))

# GBK consoles choke on printing CJK/em-dash; never let printing kill a run.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass


# ---------- generic helpers ----------

def candidates(key):
    v = SEL[key]
    return [v] if isinstance(v, str) else v


def find_actionable(page, key, timeout_ms=8000, require_enabled=False):
    """Iterate ALL matches of each candidate selector and return the first
    locator that is visible (and enabled if required). Never trust `.first`:
    Jimeng renders hidden duplicate buttons, and .first is often one of them."""
    deadline = time.time() + timeout_ms / 1000
    while True:
        for css in candidates(key):
            loc = page.locator(css)
            try:
                n = min(loc.count(), 20)
            except Exception:  # noqa: BLE001
                continue
            for i in range(n):
                el = loc.nth(i)
                try:
                    if not el.is_visible():
                        continue
                    if require_enabled and not el.is_enabled():
                        continue
                    return el
                except Exception:  # noqa: BLE001
                    continue
        if time.time() > deadline:
            return None
        time.sleep(0.3)


def screenshot_error(page, tag):
    errdir = Path("jimeng-errors")
    errdir.mkdir(exist_ok=True)
    p = errdir / f"{tag}_{int(time.time())}.png"
    try:
        page.screenshot(path=str(p), full_page=True)
    except Exception:  # noqa: BLE001
        return None
    return p


def launch(pw, profile, headless):
    ctx = pw.chromium.launch_persistent_context(
        profile, headless=headless, viewport={"width": 1440, "height": 900},
        args=["--disable-blink-features=AutomationControlled"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return ctx, page


def is_login_walled(page):
    return find_actionable(page, "login_wall", timeout_ms=2000) is not None


def open_tool(page, video=False):
    """Land on the generation surface. The old deep link redirects to
    /ai-tool/home; from there click the mode card (图片生成 / 视频生成).

    For video, ALWAYS click the video mode card: the home page has a prompt
    input of its own, so 'an input exists' does not mean the video capability
    is selected — submitting there would create the wrong task type."""
    page.goto(SEL.get("url_home", SEL["url_generate"]))
    page.wait_for_load_state("networkidle")
    key = "mode_video" if video else "mode_image"
    card = find_actionable(page, key, timeout_ms=8000)
    if card:
        card.click()
        page.wait_for_load_state("networkidle")
        return
    if find_actionable(page, "prompt_input", timeout_ms=3000):
        if video:
            print("WARNING: video mode card not found; an input exists but the "
                  "current mode is unverified - confirm the page is in video "
                  "mode before relying on this run.", file=sys.stderr)
        return
    raise RuntimeError(f"{key} card and prompt_input both missing - update selectors.json")


# ---------- prompt input (ProseMirror contenteditable) ----------

def _norm(s):
    return re.sub(r"\s+", "", s or "")


def set_prompt(page, box, text):
    """Type into the ProseMirror editor and VERIFY the text landed intact.
    keyboard.insert_text has produced '????' for CJK on some Windows setups,
    so verification is mandatory: never click submit with a corrupted prompt."""
    def clear():
        box.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Delete")

    clear()
    page.keyboard.insert_text(text)
    time.sleep(0.3)
    if _norm(box.inner_text()) == _norm(text):
        return
    # Fallback: execCommand goes through beforeinput, which ProseMirror handles.
    clear()
    box.evaluate(
        "(el, t) => { el.focus(); document.execCommand('insertText', false, t); }",
        text)
    time.sleep(0.3)
    if _norm(box.inner_text()) != _norm(text):
        raise RuntimeError(
            "prompt verification failed: editor text does not match the prompt "
            "(CJK input/encoding issue). Aborting BEFORE spending credits.")


# ---------- result extraction ----------

def collect_images(page):
    """Real result images: served from the result CDN domain and rendered
    large. Filters out avatars, icons, and asset-pool thumbnails."""
    domain = SEL.get("result_image_domain", "dreamina-sign.byteimg.com")
    min_px = SEL.get("result_min_px", 200)
    out, seen = [], set()
    for img in page.locator("img").all():
        try:
            src = img.get_attribute("src") or ""
            if domain not in src or src in seen:
                continue
            bb = img.bounding_box()
            # 16:9 results can render as small as ~240x135, so gate on the
            # LONGEST side only (icons/avatars stay well under this).
            if not bb or max(bb["width"], bb["height"]) < min_px:
                continue
            seen.add(src)
            out.append(src)
        except Exception:  # noqa: BLE001
            continue
    return out


def collect_videos(page):
    """Real result videos hide in non-visible <video> tags (bounding_box None),
    so query the DOM directly instead of relying on visibility. The loading
    animation is itself an mp4 and must be excluded."""
    markers = SEL.get("result_video_markers", ["vlabvod.com", "mime_type=video_mp4"])
    loading = SEL.get("video_loading_marker", "record-loading-animation")
    srcs = page.evaluate(
        "() => Array.from(document.querySelectorAll('video'))"
        ".flatMap(v => [v.currentSrc, v.src]).filter(Boolean)")
    out, seen = [], set()
    for s in srcs:
        if loading in s or s in seen:
            continue
        if any(m in s for m in markers):
            seen.add(s)
            out.append(s)
    return out


CTYPE_EXT = {"image/webp": ".webp", "image/png": ".png", "image/jpeg": ".jpg",
             "image/gif": ".gif", "video/mp4": ".mp4"}


def pick_ext(url, resp, video):
    """Extension must match actual content: Jimeng serves .webp images."""
    if video:
        return ".mp4"
    m = re.search(r"\.(png|jpe?g|webp|gif)(?=[?~#]|$)", url.split("?")[0], re.I)
    if m:
        return "." + m.group(1).lower().replace("jpeg", "jpg")
    ctype = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
    return CTYPE_EXT.get(ctype, ".png")


def download_all(page, urls, outdir: Path, sid, video):
    outdir.mkdir(parents=True, exist_ok=True)
    saved = []
    for i, u in enumerate(urls):
        resp = page.request.get(u)
        dest = outdir / f"{sid}_{chr(97 + i)}{pick_ext(u, resp, video)}"
        dest.write_bytes(resp.body())
        saved.append(dest.name)
    return saved


# ---------- state ----------

def state_path(a):
    if a.state:
        return Path(a.state)
    p = Path(a.prompts)
    return p.with_name(p.stem + ".jimeng-state.json")


def load_state(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else {}


def save_state(p: Path, state):
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- commands ----------

def cmd_login(a):
    with sync_playwright() as pw:
        ctx, page = launch(pw, a.profile, headless=False)
        page.goto(SEL.get("url_home", SEL["url_generate"]))
        print("Browser opened. Complete the login in the browser window.")
        input(">> Log in, wait for the home page to load, then press Enter HERE... ")
        try:
            page.goto(SEL.get("url_home", SEL["url_generate"]))
            page.wait_for_load_state("networkidle")
            print("WARNING: still seeing a login wall." if is_login_walled(page)
                  else "Login session saved.")
        except Exception as e:  # noqa: BLE001
            print(f"WARNING: could not verify login state ({e}).")
        ctx.close()


def submit_one(page, item, entry, outdir, video):
    box = find_actionable(page, "prompt_input", 10000)
    if box is None:
        raise RuntimeError("prompt_input not found - update selectors.json")
    set_prompt(page, box, item["prompt"])
    btn = find_actionable(page, "generate_button", 15000, require_enabled=True)
    if btn is None:
        raise RuntimeError("no visible+enabled generate_button - update selectors.json")
    before = collect_videos(page) if video else collect_images(page)
    btn.click()
    entry["status"] = "submitted"
    if video:
        # Video shows a credit-cost confirm dialog; nothing is spent until
        # the confirm button is clicked.
        confirm = find_actionable(page, "confirm_video_button", 20000,
                                  require_enabled=True)
        if confirm is None:
            raise RuntimeError("video confirm button not found; task NOT confirmed")
        confirm.click()
    entry["status"] = "confirmed"
    time.sleep(2)
    entry["workspace_url"] = page.url
    timeout = SEL.get("timeout_video_seconds", 600) if video \
        else SEL.get("timeout_generate_seconds", 240)
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(5)
        found = collect_videos(page) if video else collect_images(page)
        new = [s for s in found if s not in before]
        if new:
            entry["files"] = download_all(page, new, outdir, item["id"], video)
            entry["status"] = "downloaded"
            return
    raise TimeoutError(
        f"timed out after {timeout}s; workspace saved - run `resume` later: "
        f"{entry['workspace_url']}")


def cmd_generate(a):
    prompts = json.loads(Path(a.prompts).read_text(encoding="utf-8-sig"))
    sp = state_path(a)
    state = load_state(sp)
    outdir = Path(a.outdir)

    with sync_playwright() as pw:
        ctx, page = launch(pw, a.profile, headless=a.headless)
        page.goto(SEL.get("url_home", SEL["url_generate"]))
        page.wait_for_load_state("networkidle")
        if is_login_walled(page):
            ctx.close()
            sys.exit("Login required. Run: jimeng_run.py login --profile " + a.profile)

        for item in prompts:
            sid = str(item["id"])
            entry = state.setdefault(sid, {"status": "pending"})
            if entry["status"] == "downloaded":
                print(f"skip {sid} (downloaded)")
                continue
            try:
                open_tool(page, video=a.video)
                submit_one(page, item, entry, outdir, a.video)
                print(f"ok   {sid}: {entry['files']}")
            except TimeoutError as e:
                print(f"WAIT {sid}: {e}", file=sys.stderr)
            except Exception as e:  # noqa: BLE001
                shot = screenshot_error(page, sid)
                entry["status"] = "failed"
                entry["error"] = str(e)
                print(f"FAIL {sid}: {e}" + (f"\n     screenshot: {shot}" if shot else ""),
                      file=sys.stderr)
            save_state(sp, state)
            time.sleep(3)  # human-ish pacing
        ctx.close()

    stuck = [k for k, v in state.items() if v["status"] in ("submitted", "confirmed")]
    failed = [k for k, v in state.items() if v["status"] == "failed"]
    if stuck:
        print(f"pending results (run `resume` later): {stuck}")
    print(f"done. failed ids: {failed}" if failed else "done.")


def cmd_resume(a):
    """Reopen saved workspace URLs and download results that finished after
    a timeout. Costs nothing - no new generation is triggered."""
    sp = state_path(a)
    state = load_state(sp)
    targets = {k: v for k, v in state.items()
               if v.get("workspace_url") and v["status"] != "downloaded"}
    if not targets:
        print("nothing to resume")
        return
    outdir = Path(a.outdir)
    with sync_playwright() as pw:
        ctx, page = launch(pw, a.profile, headless=a.headless)
        for sid, entry in targets.items():
            try:
                page.goto(entry["workspace_url"])
                page.wait_for_load_state("networkidle")
                time.sleep(3)
                found = collect_videos(page) if a.video else collect_images(page)
                if not found:
                    print(f"WAIT {sid}: no results visible yet")
                    continue
                entry["files"] = download_all(page, found, outdir, sid, a.video)
                entry["status"] = "downloaded"
                print(f"ok   {sid}: {entry['files']}")
            except Exception as e:  # noqa: BLE001
                print(f"FAIL {sid}: {e}", file=sys.stderr)
            save_state(sp, state)
        ctx.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    lg = sub.add_parser("login")
    gen = sub.add_parser("generate")
    res = sub.add_parser("resume")
    for x in (gen, res):
        x.add_argument("--prompts", required=True)
        x.add_argument("--outdir", default="assets/images-raw")
        x.add_argument("--video", action="store_true")
        x.add_argument("--state", default=None)
        x.add_argument("--headless", action="store_true")
    for x in (lg, gen, res):
        x.add_argument("--profile", default=".jimeng-profile")
    a = ap.parse_args()
    {"login": cmd_login, "generate": cmd_generate, "resume": cmd_resume}[a.cmd](a)
