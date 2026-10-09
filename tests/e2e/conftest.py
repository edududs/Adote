"""Browser tests: the real pages, in Chromium, against a live server.

`ADOTE_CHROMIUM` points at a Chromium executable; without it, Playwright's own browser is used
(`uv run playwright install chromium`). With no browser at all the tests skip, unless
`ADOTE_REQUIRE_BROWSER=1` (set in CI) turns that into a failure.
"""

import os
from collections.abc import Generator

import pytest
from playwright.sync_api import Browser, Error, Page, sync_playwright

# Playwright's sync API runs an event loop in this thread; the ORM calls the tests make to set up
# data are still synchronous and safe here.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture(scope="session")
def browser() -> Generator[Browser]:
    with sync_playwright() as playwright:
        executable = os.environ.get("ADOTE_CHROMIUM")
        try:
            browser = (
                playwright.chromium.launch(executable_path=executable)
                if executable
                else playwright.chromium.launch()
            )
        except Error as error:
            if os.environ.get("ADOTE_REQUIRE_BROWSER") == "1":
                raise
            pytest.skip(f"no Chromium for the browser tests: {error.message.splitlines()[0]}")
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser) -> Generator[Page]:
    page = browser.new_page(viewport={"width": 1280, "height": 860}, locale="pt-BR")
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    yield page
    page.close()
    assert not errors, f"JavaScript errors: {errors}"
