from __future__ import annotations

from typing import Any


INSTALL_HINT = (
    "Automatic NBS session bootstrap requires Playwright. "
    "Install it with `uv sync --all-extras --dev`, then run "
    "`uv run playwright install chromium`."
)


def fetch_browser_cookies(
    base_url: str,
    page_route: str,
    *,
    timeout_ms: int,
    headless: bool = True,
) -> list[dict[str, Any]]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(INSTALL_HINT) from exc

    url = f"{base_url.rstrip('/')}/dg/website/page.html#/pc/national/{page_route}"
    with sync_playwright() as playwright:
        browser = None
        try:
            browser = playwright.chromium.launch(headless=headless)
            context = browser.new_context(
                locale="zh-CN",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/146.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 10_000))
            except PlaywrightTimeoutError:
                pass

            cookies: list[dict[str, Any]] = []
            for _ in range(10):
                page.wait_for_timeout(500)
                cookies = context.cookies(base_url)
                names = {cookie.get("name") for cookie in cookies}
                if {"wzws_cid", "JSESSIONID", "client_info"} & names:
                    break
            return cookies
        except PlaywrightError as exc:
            raise RuntimeError(f"{INSTALL_HINT} Playwright error: {exc}") from exc
        finally:
            if browser is not None:
                browser.close()
