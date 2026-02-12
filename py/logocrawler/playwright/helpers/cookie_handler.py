"""Cookie consent dialog handler.

Attempts to accept/dismiss cookie banners without crashing the scraping process.
"""

import sys
from playwright.async_api import Page

from ...config import COOKIE_CONSENT_SELECTORS, COOKIE_CONSENT_TIMEOUT, ENABLE_SHADOW_DOM


async def handle_cookies(page: Page) -> bool:
    """
    Attempt to accept or dismiss cookie consent dialogs.
    
    Args:
        page: Playwright page instance
        
    Returns:
        True if a cookie button was clicked, False otherwise.
        Never raises exceptions - cookie handling should not crash scraping.
    """
    for selector in COOKIE_CONSENT_SELECTORS:
        try:
            # Build locator with optional shadow DOM piercing
            if ENABLE_SHADOW_DOM:
                # Use >> to pierce shadow DOM
                locator = page.locator(selector)
            else:
                locator = page.locator(selector)
            
            # Check if element exists and is visible
            if await locator.count() > 0:
                first_button = locator.first
                
                # Wait for it to be visible and clickable
                if await first_button.is_visible():
                    await first_button.click(timeout=COOKIE_CONSENT_TIMEOUT)
                    return True
                    
        except Exception:
            # Silently continue to next selector
            continue
    
    return False


async def dismiss_overlays(page: Page) -> None:
    """
    Attempt to dismiss common overlay/modal patterns that might block scraping.
    
    This is a best-effort function that never raises exceptions.
    """
    overlay_selectors = [
        '[class*="modal"] [class*="close"]',
        '[class*="overlay"] [class*="close"]',
        '[class*="popup"] [class*="close"]',
        'button[aria-label*="close"]',
        'button[aria-label*="Close"]',
        '[class*="dismiss"]',
    ]
    
    for selector in overlay_selectors:
        try:
            locator = page.locator(selector)
            if await locator.count() > 0:
                first_elem = locator.first
                if await first_elem.is_visible():
                    await first_elem.click(timeout=1000)
                    return
        except Exception:
            continue
