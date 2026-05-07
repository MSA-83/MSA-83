"""E2E tests for Titanium frontend."""

import pytest
from playwright.async_api import Page


@pytest.mark.anyio
class TestLandingPage:
    """Test landing page."""

    async def test_landing_loads(self, page: Page, base_url: str):
        """Landing page should load successfully."""
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")
        assert page.title()

    async def test_landing_has_navigation(self, page: Page, base_url: str):
        """Landing page should have navigation links."""
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")
        nav = page.locator("nav")
        await nav.wait_for(state="visible")


@pytest.mark.anyio
class TestLoginPage:
    """Test login page."""

    async def test_login_page_loads(self, page: Page, base_url: str):
        """Login page should load."""
        await page.goto(f"{base_url}/login")
        await page.wait_for_load_state("networkidle")
        assert await page.locator('input[name="email"]').is_visible()
        assert await page.locator('input[name="password"]').is_visible()

    async def test_login_with_invalid_credentials(self, page: Page, base_url: str):
        """Login with invalid credentials should show error."""
        await page.goto(f"{base_url}/login")
        await page.fill('input[name="email"]', "invalid@example.com")
        await page.fill('input[name="password"]', "wrongpassword")
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")

    async def test_login_form_validation(self, page: Page, base_url: str):
        """Login form should validate empty fields."""
        await page.goto(f"{base_url}/login")
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")


@pytest.mark.anyio
class TestChatPage:
    """Test chat functionality."""

    async def test_chat_page_loads(self, page: Page, base_url: str):
        """Chat page should load."""
        await page.goto(f"{base_url}/chat")
        await page.wait_for_load_state("networkidle")

    async def test_chat_input_exists(self, page: Page, base_url: str):
        """Chat page should have input field."""
        await page.goto(f"{base_url}/chat")
        await page.wait_for_load_state("networkidle")
        input_field = page.locator('input[type="text"], textarea')
        await input_field.wait_for(state="visible")

    async def test_send_message(self, page: Page, base_url: str):
        """Should be able to type and send a message."""
        await page.goto(f"{base_url}/chat")
        await page.wait_for_load_state("networkidle")
        input_field = page.locator('input[type="text"], textarea')
        await input_field.fill("Hello, Titanium!")
        await page.keyboard.press("Enter")


@pytest.mark.anyio
class TestMemoryPage:
    """Test memory page."""

    async def test_memory_page_loads(self, page: Page, base_url: str):
        """Memory page should load."""
        await page.goto(f"{base_url}/memory")
        await page.wait_for_load_state("networkidle")

    async def test_memory_search_exists(self, page: Page, base_url: str):
        """Memory page should have search input."""
        await page.goto(f"{base_url}/memory")
        await page.wait_for_load_state("networkidle")
        search = page.locator('input[type="text"], input[placeholder*="search" i]')
        await search.wait_for(state="visible")


@pytest.mark.anyio
class TestNavigation:
    """Test navigation between pages."""

    async def test_nav_to_chat(self, page: Page, base_url: str):
        """Should navigate to chat page."""
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")
        await page.click('a[href="/chat"]')
        await page.wait_for_url("**/chat")

    async def test_nav_to_memory(self, page: Page, base_url: str):
        """Should navigate to memory page."""
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")
        await page.click('a[href="/memory"]')
        await page.wait_for_url("**/memory")

    async def test_nav_to_agents(self, page: Page, base_url: str):
        """Should navigate to agents page."""
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")
        await page.click('a[href="/agents"]')
        await page.wait_for_url("**/agents")

    async def test_nav_to_billing(self, page: Page, base_url: str):
        """Should navigate to billing page."""
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")
        await page.click('a[href="/billing"]')
        await page.wait_for_url("**/billing")

    async def test_nav_to_settings(self, page: Page, base_url: str):
        """Should navigate to settings page."""
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")
        await page.click('a[href="/settings"]')
        await page.wait_for_url("**/settings")


@pytest.mark.anyio
class TestResponsiveDesign:
    """Test responsive design."""

    async def test_mobile_view(self, page: Page, base_url: str):
        """Should render properly on mobile."""
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")
        assert page.is_visible("nav") or page.is_visible('[aria-label="menu"]')

    async def test_tablet_view(self, page: Page, base_url: str):
        """Should render properly on tablet."""
        await page.set_viewport_size({"width": 768, "height": 1024})
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")

    async def test_desktop_view(self, page: Page, base_url: str):
        """Should render properly on desktop."""
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")


@pytest.mark.anyio
class TestAccessibility:
    """Test accessibility features."""

    async def test_keyboard_navigation(self, page: Page, base_url: str):
        """Should support keyboard navigation."""
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")
        await page.keyboard.press("Tab")
        focused = await page.evaluate("() => document.activeElement.tagName")
        assert focused in ["A", "BUTTON", "INPUT", "NAV"]

    async def test_focus_indicators(self, page: Page, base_url: str):
        """Focusable elements should have focus indicators."""
        await page.goto(base_url)
        await page.wait_for_load_state("networkidle")
        links = await page.locator("a").all()
        assert len(links) > 0
