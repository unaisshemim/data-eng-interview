"""Anti-blocking utilities for Playwright crawler.

Provides:
- User-agent rotation
- Viewport rotation
- Random delays for rate limiting
- Captcha detection
"""

import random
import asyncio
from typing import Dict
from playwright.async_api import Page

from ...config import (
    USER_AGENTS,
    VIEWPORTS,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
)


def get_random_user_agent() -> str:
    """Return a random user-agent string from the pool."""
    return random.choice(USER_AGENTS)


def get_random_viewport() -> Dict[str, int]:
    """Return a random viewport dict with width and height."""
    return random.choice(VIEWPORTS).copy()


async def random_delay() -> None:
    """
    Sleep for a random duration between REQUEST_DELAY_MIN and REQUEST_DELAY_MAX.
    
    Used for rate limiting to avoid detection patterns.
    """
    delay_ms = random.randint(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
    await asyncio.sleep(delay_ms / 1000)


# Common captcha indicators
CAPTCHA_INDICATORS = [
    # reCAPTCHA
    'iframe[src*="recaptcha"]',
    'iframe[src*="google.com/recaptcha"]',
    '#recaptcha',
    '.g-recaptcha',
    
    # hCaptcha
    'iframe[src*="hcaptcha"]',
    '.h-captcha',
    '#hcaptcha',
    
    # Cloudflare
    '#cf-wrapper',
    '#challenge-running',
    '#challenge-form',
    '.cf-browser-verification',
    
    # Generic challenge pages
    '#challenge-stage',
    '.captcha-container',
    '[class*="captcha"]',
    '[id*="captcha"]',
]

CAPTCHA_TEXT_INDICATORS = [
    "verify you are human",
    "are you a robot",
    "please verify",
    "security check",
    "checking your browser",
    "just a moment",
    "ddos protection",
    "attention required",
    "access denied",
    "blocked",
]


async def detect_captcha(page: Page) -> bool:
    """
    Check if the current page contains captcha or challenge elements.
    
    Args:
        page: Playwright page instance
        
    Returns:
        True if captcha/challenge detected, False otherwise
    """
    try:
        # Check for captcha elements
        for selector in CAPTCHA_INDICATORS:
            try:
                element = await page.query_selector(selector)
                if element:
                    return True
            except Exception:
                pass
        
        # Check page text for captcha indicators
        try:
            body_text = await page.evaluate("() => document.body?.innerText?.toLowerCase() || ''")
            for indicator in CAPTCHA_TEXT_INDICATORS:
                if indicator in body_text:
                    return True
        except Exception:
            pass
        
        # Check page title for common challenge titles
        try:
            title = await page.title()
            title_lower = title.lower()
            challenge_titles = ["just a moment", "attention required", "access denied", "security"]
            for ct in challenge_titles:
                if ct in title_lower:
                    return True
        except Exception:
            pass
        
        return False
        
    except Exception:
        # If detection fails, assume no captcha to avoid false positives
        return False
