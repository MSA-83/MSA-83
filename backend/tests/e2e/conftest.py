"""Playwright E2E test configuration."""

import asyncio
import os

import pytest
from playwright.async_api import Browser, BrowserContext, Page, async_playwright


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def browser():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=os.getenv("HEADLESS", "true").lower() == "true",
        )
        yield browser
        await browser.close()


@pytest.fixture
async def context(browser: Browser) -> BrowserContext:
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
    )
    yield context
    await context.close()


@pytest.fixture
async def page(context: BrowserContext) -> Page:
    page = await context.new_page()
    yield page


@pytest.fixture
def base_url() -> str:
    return os.getenv("BASE_URL", "http://localhost:3000")


@pytest.fixture
def api_url() -> str:
    return os.getenv("API_URL", "http://localhost:8000")
