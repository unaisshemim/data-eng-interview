"""Domain processor with retry stages.

Processes a single domain through multiple retry stages:
- R1: 5 second timeout
- R2: 7 second timeout (if R1 fails)
- R3: 9 second timeout (if R2 fails)

Also handles URL variants (https://, https://www., http://, http://www.)
"""

import sys
from typing import Tuple, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from ...config import PHASE_1_TIMEOUT, PHASE_R1_TIMEOUT, PHASE_R3_TIMEOUT
from ...utils.validators import sanitize_domain
from .logo_extractor import extract_logo, extract_favicon
from .cookie_handler import handle_cookies, dismiss_overlays


# URL variants to try in order
URL_VARIANTS = [
    "https://{}",
    "https://www.{}",
    "http://{}",
    "http://www.{}",
]


async def process_domain(page: Page, domain: str) -> Tuple[str, str]:
    """
    Process a single domain with retry stages.
    
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
        
        logo = await _process_url_with_retries(page, url)
        if logo:
            return (domain, logo)
    
    # All variants failed
    return (domain, "")


async def _process_url_with_retries(page: Page, url: str) -> str:
    """
    Process a URL through retry stages R1 -> R2 -> R3.
    
    Args:
        page: Playwright page instance
        url: Full URL to navigate to
        
    Returns:
        Logo URL if found, empty string otherwise.
    """
    try:
        # Initial navigation with R1 timeout
        await page.goto(
            url,
            timeout=PHASE_1_TIMEOUT,
            wait_until="domcontentloaded"
        )
    except PlaywrightTimeout:
        # Navigation timeout - try next URL variant
        return ""
    except Exception as e:
        # Network error or other issue
        return ""
    
    # Handle cookies/popups (non-blocking)
    try:
        await handle_cookies(page)
        await dismiss_overlays(page)
    except Exception:
        pass
    
    # R1: First extraction attempt (page just loaded)
    logo = await extract_logo(page)
    if logo:
        return logo
    
    # R2: Wait additional time and retry
    try:
        # Wait for more content to load
        await page.wait_for_load_state("load", timeout=PHASE_R1_TIMEOUT - PHASE_1_TIMEOUT)
    except PlaywrightTimeout:
        pass
    except Exception:
        pass
    
    logo = await extract_logo(page)
    if logo:
        return logo
    
    # R3: Final wait and retry
    try:
        # Wait for network to be idle
        await page.wait_for_load_state("networkidle", timeout=PHASE_R3_TIMEOUT - PHASE_R1_TIMEOUT)
    except PlaywrightTimeout:
        pass
    except Exception:
        pass
    
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
