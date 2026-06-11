#!/usr/bin/env python3
"""Playwright automation for Jimeng (即梦) image generation.

Usage:
    python jimeng_run.py login    --profile .jimeng-profile
    python jimeng_run.py generate --profile .jimeng-profile \
        --prompts prompts.json --outdir assets/images-raw [--headless]

prompts.json: [{"id": "1", "prompt": "...", "count": 1}, ...]
State checkpoint: jimeng-state.json (completed ids are skipped on rerun).
Selectors: selectors.json next to this script — edit THAT file when the UI changes.

Requires: pip install playwright && playwright install chromium
"""
import argparse
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
SEL = json.loads((HERE / "selectors.json").read_text(encoding="utf-8"))


def first_visible(page, key, timeout=5000):
    """Try selector candidates in order; return the first visible locator or None."""
    candidates = SEL[key]
    if isinstance(candidates, str):
        candidates = [candidates]
    for css in candidates:
        loc = page.locator(css).first
        try:
            loc.wait_for(state="visible", timeout=timeout)
            return loc
        except Exception:  # noqa: BLE001
            continue
    return None


def screenshot_error(page, tag):
    errdir = Path("jimeng-errors")
    errdir.mkdir(exist_ok=True)
    p = errdir / f"{tag}_{int(time.time())}.png"
    page.screenshot(path=str(p), full_page=True)
    return p


def launch(pw, profile, headless):
    ctx = pw.chromium.launch_persistent_context(
        profile, headless=headless, viewport={"width": 1440, "height": 900},
        args=["--disable-blink-features=AutomationControlled"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return ctx, page


def cmd_login(a):
    with sync_playwright() as pw:
        ctx, page = launch(pw, a.profile, headless=False)
        page.goto(SEL["url_generate"])
        print("Browser opened. Complete the login in the browser window.")
        input(">> Log in, wait until the generate page is fully loaded, "
              "then press Enter HERE to save the session... ")
        try:
            page.goto(SEL["url_generate"])
            page.wait_for_load_state("networkidle")
            if is_login_walled(page):
                print("WARNING: still seeing a login wall — session may not be saved. "
                      "Rerun login if generate fails.")
            else:
                print("Login session saved.")
        except Exception as e:  # noqa: BLE001
            print(f"WARNING: could not verify login state ({e}); session saved as-is.")
        ctx.close()


def is_login_walled(page):
    if isinstance(SEL["login_wall"], str):
        walls = [SEL["login_wall"]]
    else:
        walls = SEL["login_wall"]
    return any(page.locator(w).first.is_visible() for w in walls
               if page.locator(w).count() > 0)


def generate_one(page, item, outdir: Path):
    box = first_visible(page, "prompt_input", timeout=10000)
    if box is None:
        raise RuntimeError("prompt_input not found — update selectors.json")
    box.click()
    box.fill(item["prompt"])
    btn = first_visible(page, "generate_button")
    if btn is None:
        raise RuntimeError("generate_button not found — update selectors.json")
    before = page.locator(SEL["result_container"][0] if isinstance(
        SEL["result_container"], list) else SEL["result_container"]).count()
    btn.click()

    deadline = time.time() + SEL.get("timeout_generate_seconds", 180)
    container_sel = (SEL["result_container"][0] if isinstance(SEL["result_container"], list)
                     else SEL["result_container"])
    while time.time() < deadline:
        time.sleep(5)
        gen = first_visible(page, "generating_indicator", timeout=1000)
        if gen is None and page.locator(container_sel).count() > before:
            break
    else:
        raise RuntimeError(f"timeout waiting for generation of id={item['id']}")

    newest = page.locator(container_sel).first
    imgs = newest.locator(SEL["result_image"])
    n = imgs.count()
    if n == 0:
        raise RuntimeError(f"no result images for id={item['id']}")
    saved = []
    for i in range(n):
        src = imgs.nth(i).get_attribute("src")
        if not src or src.startswith("data:image/svg"):
            continue
        dest = outdir / f"{item['id']}_{chr(97 + i)}.png"
        resp = page.request.get(src)
        dest.write_bytes(resp.body())
        saved.append(dest.name)
    return saved


def cmd_generate(a):
    prompts = json.loads(Path(a.prompts).read_text(encoding="utf-8"))
    state_p = Path("jimeng-state.json")
    state = json.loads(state_p.read_text(encoding="utf-8")) if state_p.exists() else {}
    outdir = Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        ctx, page = launch(pw, a.profile, headless=a.headless)
        page.goto(SEL["url_generate"])
        page.wait_for_load_state("networkidle")
        if is_login_walled(page):
            ctx.close()
            sys.exit("Login required. Run: jimeng_run.py login --profile " + a.profile)

        for item in prompts:
            sid = str(item["id"])
            if state.get(sid) == "done":
                print(f"skip {sid} (done)")
                continue
            try:
                saved = generate_one(page, item, outdir)
                state[sid] = "done"
                print(f"ok   {sid}: {saved}")
            except Exception as e:  # noqa: BLE001
                shot = screenshot_error(page, sid)
                state[sid] = "failed"
                print(f"FAIL {sid}: {e}\n     screenshot: {shot}", file=sys.stderr)
            state_p.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                               encoding="utf-8")
            time.sleep(3)  # human-ish pacing between prompts
        ctx.close()

    failed = [k for k, v in state.items() if v == "failed"]
    print(f"done. failed ids: {failed}" if failed else "done. all ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    lg = sub.add_parser("login")
    gen = sub.add_parser("generate")
    gen.add_argument("--prompts", required=True)
    gen.add_argument("--outdir", default="assets/images-raw")
    gen.add_argument("--headless", action="store_true")
    for x in (lg, gen):
        x.add_argument("--profile", default=".jimeng-profile")
    a = ap.parse_args()
    cmd_login(a) if a.cmd == "login" else cmd_generate(a)
