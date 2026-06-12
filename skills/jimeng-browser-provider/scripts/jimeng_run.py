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
Reserved (accepted, not yet implemented): "reference_image" (path to a style
anchor for image-to-image), "image_to_image" (bool). Unknown keys are ignored,
so adding them today is forward-compatible.
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
        try:
            card.click(timeout=5000)
            page.wait_for_load_state("networkidle")
        except Exception:  # noqa: BLE001
            # An already-active card intercepts pointer events; that's fine
            # as long as the prompt editor is reachable.
            if not find_actionable(page, "prompt_input", timeout_ms=3000):
                raise
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

def result_root(page):
    """Scope image search to the LAST result card in the workspace, so old
    generations in the conversation history are not re-collected (a full-page
    scan once returned 27 stale thumbnails). Falls back to the whole page."""
    if "result_scope" not in SEL:
        return page
    for css in candidates("result_scope"):
        loc = page.locator(css)
        try:
            n = loc.count()
        except Exception:  # noqa: BLE001
            continue
        for i in range(n - 1, -1, -1):
            el = loc.nth(i)
            try:
                if el.is_visible() and el.locator("img").count() > 0:
                    return el
            except Exception:  # noqa: BLE001
                continue
    return page


def collect_image_elements(page):
    """Result images inside the newest result card: CDN domain + rendered
    size filtered, capped at max_results_per_task (newest last in DOM order).
    Returns (locator, src) pairs — the locator is needed for HD download."""
    domain = SEL.get("result_image_domain", "dreamina-sign.byteimg.com")
    min_px = SEL.get("result_min_px", 200)
    cap = SEL.get("max_results_per_task", 8)
    root = result_root(page)
    out, seen = [], set()
    for img in root.locator("img").all():
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
            out.append((img, src))
        except Exception:  # noqa: BLE001
            continue
    return out[-cap:]


def collect_images(page):
    return [src for _, src in collect_image_elements(page)]


def image_size(path: Path):
    """Read pixel dimensions of png/jpeg/webp without external deps."""
    try:
        return image_size_bytes(path.read_bytes())
    except Exception:  # noqa: BLE001
        return None


def image_size_bytes(d: bytes):
    try:
        if d[:8] == b"\x89PNG\r\n\x1a\n":
            return (int.from_bytes(d[16:20], "big"), int.from_bytes(d[20:24], "big"))
        if d[:3] == b"\xff\xd8\xff":  # JPEG: scan for SOF marker
            i = 2
            sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                   0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
            while i < len(d) - 9:
                if d[i] != 0xFF:
                    i += 1
                    continue
                if d[i + 1] in sof:
                    return (int.from_bytes(d[i + 7:i + 9], "big"),
                            int.from_bytes(d[i + 5:i + 7], "big"))
                i += 2 + int.from_bytes(d[i + 2:i + 4], "big")
        if d[:4] == b"RIFF" and d[8:12] == b"WEBP":
            fmt = d[12:16]
            if fmt == b"VP8X":
                return (1 + int.from_bytes(d[24:27], "little"),
                        1 + int.from_bytes(d[27:30], "little"))
            if fmt == b"VP8 ":
                return (int.from_bytes(d[26:28], "little") & 0x3FFF,
                        int.from_bytes(d[28:30], "little") & 0x3FFF)
            if fmt == b"VP8L":
                b = d[21:25]
                return (1 + (((b[1] & 0x3F) << 8) | b[0]),
                        1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6)))
    except Exception:  # noqa: BLE001
        pass
    return None


SAFE_IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def safe_ext(filename, fallback=".png"):
    """Never trust suggested_filename: sanitize and whitelist the suffix."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename or "")
    s = Path(cleaned).suffix.lower()
    return s if s in SAFE_IMG_EXTS else fallback


def modal_image_candidates(page, exclude_srcs):
    """All images rendered after the modal opened, ranked by naturalWidth
    (intrinsic resolution — far more truthful than the on-screen box)."""
    domain = SEL.get("result_image_domain", "dreamina-sign.byteimg.com")
    try:
        imgs = page.evaluate(
            "() => Array.from(document.images).map(im => ("
            "{src: im.currentSrc || im.src, nw: im.naturalWidth, nh: im.naturalHeight}))")
    except Exception:  # noqa: BLE001
        return []
    out = []
    for it in imgs:
        s = it.get("src") or ""
        if domain not in s or s in exclude_srcs:
            continue
        out.append((s, max(it.get("nw") or 0, it.get("nh") or 0)))
    out.sort(key=lambda x: -x[1])
    return out


def hd_url_variants(src):
    """The thumbnail URL embeds an imageX resize template, e.g.
    `aigc_resize_loss:480:480`. Rewriting the numbers often yields the
    original asset from the same signed URL."""
    marker = SEL.get("resize_marker", "aigc_resize_loss")
    out = []
    for rep in ("0:0", "4096:4096", "2048:2048"):
        v = re.sub(re.escape(marker) + r":\d+:\d+", f"{marker}:{rep}", src)
        if v != src:
            out.append(v)
    return out


def fetch_best(page, urls, cap=6):
    """Fetch candidate URLs, verify each is a real image, return the one
    with the largest pixel dimensions: (size, body, url, content_type)."""
    best = None
    for u in urls[:cap]:
        try:
            resp = page.request.get(u)
            if not resp.ok:
                continue
            body = resp.body()
            size = image_size_bytes(body)
            if not size:
                continue
            if best is None or max(size) > max(best[0]):
                best = (size, body, u, (resp.headers.get("content-type") or ""))
        except Exception:  # noqa: BLE001
            continue
    return best


def dump_modal_debug(page, sid):
    """When the download control isn't found, dump everything a human needs
    to identify it: visible buttons/icons (class, aria-label, title, text)
    and all image srcs with natural sizes. Written to jimeng-errors/."""
    try:
        info = page.evaluate(
            """() => {
              const els = Array.from(document.querySelectorAll(
                "button, [role='button'], svg, [class*='icon'], [class*='Icon']"));
              const buttons = els.slice(0, 300).map(e => {
                const r = e.getBoundingClientRect();
                return {tag: e.tagName,
                        cls: ((e.className && e.className.baseVal) || e.className || '').toString().slice(0, 150),
                        aria: e.getAttribute('aria-label'),
                        title: e.getAttribute('title'),
                        text: (e.innerText || '').slice(0, 30),
                        w: Math.round(r.width), h: Math.round(r.height)};
              }).filter(b => b.w > 0 && b.h > 0);
              const images = Array.from(document.images).map(im => {
                const r = im.getBoundingClientRect();
                return {src: (im.currentSrc || im.src).slice(0, 300),
                        w: Math.round(r.width), h: Math.round(r.height),
                        nw: im.naturalWidth, nh: im.naturalHeight};
              });
              return {buttons, images};
            }""")
        errdir = Path("jimeng-errors")
        errdir.mkdir(exist_ok=True)
        p = errdir / f"{sid}_modal_{int(time.time())}.json"
        p.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        screenshot_error(page, f"{sid}_modal")
        print(f"DEBUG: modal candidates dumped -> {p}", file=sys.stderr)
    except Exception:  # noqa: BLE001
        pass


def watch_downloads_dir(since_ts, timeout_s=120):
    """Fallback capture: poll the browser's download folder (configurable
    `downloads_dir` in selectors.json) for a new finished jimeng-* file."""
    ddir = SEL.get("downloads_dir")
    if not ddir:
        return None
    ddir = Path(ddir)
    if not ddir.is_dir():
        return None
    pattern = SEL.get("download_glob", "jimeng-*")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for p in ddir.glob(pattern):
            try:
                if p.suffix in (".crdownload", ".tmp", ".part"):
                    continue
                if p.stat().st_mtime < since_ts - 2:
                    continue
                s1 = p.stat().st_size
                time.sleep(1.5)
                if s1 > 0 and p.stat().st_size == s1:   # size stable = finished
                    return p
            except OSError:
                continue
        time.sleep(2)
    return None


def hd_download_one(page, img, src, base: Path, all_thumb_srcs, sid):
    """Try hardest to get the ORIGINAL file, not the ~270px display thumbnail.

    1. Click the thumbnail to open the preview modal; click its download
       control if one is found (browser download = original).
       If no control matches, dump button/img diagnostics to jimeng-errors/
       so the real selector can be identified and added to selectors.json.
    2. Build candidate URLs: modal images ranked by naturalWidth whose URL
       has NO resize template, plus resize-template rewrites
       (`aigc_resize_loss:480:480` -> `0:0` / `4096:4096` / `2048:2048`)
       of the best modal src and the thumbnail src. Fetch them all, measure
       actual pixels, keep the largest.
    3. Else fall back to the thumbnail src (will be flagged low_resolution).
    Returns (dest_path, method, content_type)."""
    marker = SEL.get("resize_marker", "aigc_resize_loss")
    modal_open = False
    try:
        img.click()
        page.wait_for_timeout(1200)
        modal_open = True
        btn = find_actionable(page, "download_button", 4000)
        if btn:
            click_ts = time.time()
            try:
                # Originals are MB-scale and the export is slow: wait long.
                with page.expect_download(
                        timeout=SEL.get("download_timeout_ms", 120000)) as dl:
                    btn.click()
                d = dl.value
                dest = base.with_suffix(safe_ext(d.suggested_filename))
                d.save_as(dest)
                return dest, "preview_download", ""
            except Exception:  # noqa: BLE001
                # Some download paths bypass Playwright's download event;
                # watch the browser's download folder for the new file.
                got = watch_downloads_dir(click_ts)
                if got:
                    dest = base.with_suffix(safe_ext(got.name))
                    dest.write_bytes(got.read_bytes())
                    return dest, "downloads_dir", ""
        else:
            dump_modal_debug(page, sid)

        cands = modal_image_candidates(page, all_thumb_srcs)
        urls = [s for s, _ in cands if marker not in s]      # clean originals first
        for s, _ in cands[:2]:                                # then template rewrites
            urls.extend(hd_url_variants(s))
        urls.extend(hd_url_variants(src))
        urls = list(dict.fromkeys(urls))
        best = fetch_best(page, urls)
        if best:
            size, body, u, ctype = best
            dest = base.with_suffix(ext_for(u, ctype))
            dest.write_bytes(body)
            method = "preview_src" if any(u == s for s, _ in cands) else "hd_url_variant"
            return dest, method, ctype
    except Exception:  # noqa: BLE001
        pass
    finally:
        if modal_open:
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)
            except Exception:  # noqa: BLE001
                pass
    resp = page.request.get(src)
    dest = base.with_suffix(pick_ext(src, resp, False))
    dest.write_bytes(resp.body())
    return dest, "thumbnail_fallback", (resp.headers.get("content-type") or "")


def download_images(page, elems, outdir: Path, sid, entry):
    """HD-first image download with mandatory quality verification.

    Every saved file is measured (png/jpg/webp header parse); if ANY file's
    longest side is below `min_download_long_px`, the entry is marked
    `low_resolution`, NOT `downloaded` — `generate` then skips it (no credit
    re-spend) and `resume` retries the HD fetch from the saved workspace."""
    outdir.mkdir(parents=True, exist_ok=True)
    min_long = SEL.get("min_download_long_px", 1024)
    prod_methods = set(SEL.get("production_methods",
                               ["preview_download", "downloads_dir", "hd_url_variant"]))
    all_thumb_srcs = {s for _, s in elems}
    files, low = [], False
    for i, (img, src) in enumerate(elems):
        base = outdir / f"{sid}_{i + 1:03d}"   # _001-style: safe past 26 items
        dest, method, ctype = hd_download_one(page, img, src, base,
                                              all_thumb_srcs, sid)
        size = image_size(dest)
        meta = {"file": dest.name, "bytes": dest.stat().st_size,
                "width": size[0] if size else None,
                "height": size[1] if size else None,
                "content_type": ctype, "source_url": src, "method": method}
        # Production bar: real-download method AND real pixels. preview_src /
        # thumbnail_fallback are stopgaps and never count as `downloaded`.
        if not size or max(size) < min_long:
            low = True
            meta["note"] = f"below min_download_long_px={min_long}"
        elif method not in prod_methods:
            low = True
            meta["note"] = f"method '{method}' not in production_methods"
        files.append(meta)
    entry["files"] = files
    entry["status"] = "low_resolution" if low else "downloaded"
    return files


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


def ext_for(url, ctype):
    m = re.search(r"\.(png|jpe?g|webp|gif)(?=[?~#]|$)", url.split("?")[0], re.I)
    if m:
        return "." + m.group(1).lower().replace("jpeg", "jpg")
    return CTYPE_EXT.get((ctype or "").split(";")[0].strip().lower(), ".png")


def pick_ext(url, resp, video):
    """Extension must match actual content: Jimeng serves .webp images."""
    if video:
        return ".mp4"
    return ext_for(url, resp.headers.get("content-type") if resp else "")


def download_all(page, urls, outdir: Path, sid, video):
    outdir.mkdir(parents=True, exist_ok=True)
    saved = []
    for i, u in enumerate(urls):
        resp = page.request.get(u)
        # _001-style numbering: chr(97+i) breaks past 26 items ('{', '|'...)
        dest = outdir / f"{sid}_{i + 1:03d}{pick_ext(u, resp, video)}"
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
    # The page must move to the real result workspace (.../generate?workspace=...).
    # NEVER record /home as workspace_url: resume would land on the public feed
    # and scrape strangers' works. Wait for the navigation; keep watching during
    # the result loop if it hasn't happened yet.
    marker = SEL.get("workspace_url_marker", "workspace=")
    for _ in range(30):
        if marker in page.url:
            break
        time.sleep(1)
    entry["workspace_url"] = page.url if marker in page.url else None
    if not entry["workspace_url"]:
        print(f"WARNING: no workspace URL yet for {item['id']} - will keep watching",
              file=sys.stderr)
    timeout = SEL.get("timeout_video_seconds", 600) if video \
        else SEL.get("timeout_generate_seconds", 240)
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(5)
        if not entry.get("workspace_url") and marker in page.url:
            entry["workspace_url"] = page.url
        if video:
            new = [s for s in collect_videos(page) if s not in before]
            if new:
                entry["files"] = download_all(page, new, outdir, item["id"], True)
                entry["status"] = "downloaded"
                return
        else:
            new = [(el, s) for el, s in collect_image_elements(page)
                   if s not in before]
            if new:
                download_images(page, new, outdir, item["id"], entry)
                return
    raise TimeoutError(
        f"timed out after {timeout}s; workspace saved - run `resume` later: "
        f"{entry.get('workspace_url') or 'NO WORKSPACE URL CAPTURED'}")


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
            if entry["status"] == "low_resolution":
                # regenerating would spend credits; the HD original already
                # exists in the workspace - resume retries the download.
                print(f"skip {sid} (low_resolution - run `resume` to refetch HD)")
                continue
            try:
                open_tool(page, video=a.video)
                submit_one(page, item, entry, outdir, a.video)
                print(f"{entry['status']:<4} {sid}: {entry['files']}")
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
    marker = SEL.get("workspace_url_marker", "workspace=")
    targets, bad = {}, []
    for k, v in state.items():
        if v["status"] == "downloaded" or not v.get("workspace_url"):
            continue
        if marker not in v["workspace_url"]:
            bad.append(k)   # e.g. /home recorded by an older buggy run
            continue
        targets[k] = v
    if bad:
        print(f"SKIP {bad}: workspace_url is not a result workspace "
              "(old bug recorded /home) - regenerate or fix state manually",
              file=sys.stderr)
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
                if a.video:
                    found = collect_videos(page)
                    if not found:
                        print(f"WAIT {sid}: no results visible yet")
                        continue
                    entry["files"] = download_all(page, found, outdir, sid, True)
                    entry["status"] = "downloaded"
                else:
                    elems = collect_image_elements(page)
                    if not elems:
                        print(f"WAIT {sid}: no results visible yet")
                        continue
                    download_images(page, elems, outdir, sid, entry)
                print(f"{entry['status']:<4} {sid}: {entry['files']}")
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
