"""Domain processor with single-pass extraction.

Processes a single domain with:
- Single navigation attempt per URL variant
- domcontentloaded wait + small delay (no networkidle)
- Captcha detection and skip
- Hard timeout enforced at browser_manager level
"""

import sys
from typing import Tuple, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from ...config import NAV_TIMEOUT, POST_NAV_DELAY
from ...utils.validators import sanitize_domain
from .logo_extractor import extract_logo, extract_favicon
from .cookie_handler import handle_cookies, dismiss_overlays
from .anti_blocking import detect_captcha


# URL variants to try in order
URL_VARIANTS = [
    "https://{}",
    "https://www.{}",
    "http://{}",
    "http://www.{}",
]


async def process_domain(page: Page, domain: str) -> Tuple[str, str]:
    """
    Process a single domain with single-pass extraction.
    
    Tries URL variants (https, https://www, http, http://www) sequentially.
    Each attempt uses domcontentloaded + small delay.
    Hard per-domain timeout is enforced at the browser_manager level.
    
    Args:
        page: Playwright page instance
        domain: Domain to process (e.g., "example.com")
        
    Returns:
        Tuple of (domain, logo_url). logo_url is empty string if not found.
    """
    # Sanitize domain
    clean_domain = sanitize_domain(domain)
    if not clean_domain:
        return (domain, "")
    
    # Try each URL variant
    for url_template in URL_VARIANTS:
        url = url_template.format(clean_domain)
        
        logo = await _process_url(page, url)
        if logo:
            return (domain, logo)
    
    # All variants failed
    return (domain, "")


async def _process_url(page: Page, url: str) -> str:
    """
    Process a single URL with single navigation attempt.
    
    Uses domcontentloaded + POST_NAV_DELAY instead of networkidle.
    Includes captcha detection to skip blocked pages early.
    
    Args:
        page: Playwright page instance
        url: Full URL to navigate to
        
    Returns:
        Logo URL if found, empty string otherwise.
    """
    try:
        # Navigate with domcontentloaded (faster than networkidle)
        await page.goto(
            url,
            timeout=NAV_TIMEOUT,
            wait_until="domcontentloaded"
        )
    except PlaywrightTimeout:
        # Navigation timeout - try next URL variant
        return ""
    except Exception:
        # Network error or other issue
        return ""
    
    # Small delay to let JS render (replaces networkidle)
    try:
        await page.wait_for_timeout(POST_NAV_DELAY)
    except Exception:
        pass
    
    # Check for captcha/challenge page
    try:
        if await detect_captcha(page):
            sys.stderr.write(f"[PW] Captcha detected: {url}\n")
            return ""
    except Exception:
        pass
    
    # Handle cookies/popups (non-blocking)
    try:
        await handle_cookies(page)
        await dismiss_overlays(page)
    except Exception:
        pass
    
    # Extract logo
    logo = await extract_logo(page)
    if logo:
        return logo
    
    # Fallback: try favicon
    logo = await extract_favicon(page)
    if logo:
        return logo
    
    return ""


async def process_domain_playwright(browser, domain: str) -> Tuple[str, str]:
    """
    Standalone function for single domain testing.
    
    Creates a new page, processes domain, and closes page.
    
    Args:
        browser: Playwright browser instance
        domain: Domain to process
        
    Returns:
        Tuple of (domain, logo_url)
    """
    context = await browser.new_context()
    page = await context.new_page()
    
    try:
        result = await process_domain(page, domain)
        return result
    finally:
        await page.close()
        await context.close()
