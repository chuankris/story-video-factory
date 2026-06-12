#!/usr/bin/env python3
"""No-credit smoke test for jimeng-browser-provider.

Opens jimeng.jianying.com with a FRESH (logged-out) temp profile and asserts:
  1. the page loads,
  2. the login wall is detected by is_login_walled(),
  3. therefore generate would refuse before spending any credits.

Never submits a prompt; costs nothing.

Run from repo root:  python tests/smoke_jimeng.py
Requires: pip install playwright && playwright install chromium
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "jimeng-browser-provider" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from playwright.sync_api import sync_playwright  # noqa: E402

import jimeng_run  # noqa: E402


def main():
    with tempfile.TemporaryDirectory(prefix="jimeng-smoke-") as tmp_profile:
        with sync_playwright() as pw:
            ctx, page = jimeng_run.launch(pw, tmp_profile, headless=True)
            url = jimeng_run.SEL.get("url_home", jimeng_run.SEL["url_generate"])
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)
            final_url = page.url
            walled = jimeng_run.is_login_walled(page)
            ctx.close()

    print(f"loaded: {final_url}")
    if not walled:
        sys.exit(
            "SMOKE TEST FAILED: fresh profile did NOT trigger login-wall detection.\n"
            "Either the site changed its login UI (update login_wall in selectors.json) "
            "or the page did not load. A real generate run would NOT be blocked correctly.")
    print("login wall detected on fresh profile -> generate would stop before spending credits")
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
