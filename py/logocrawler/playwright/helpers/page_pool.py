"""Page pool for efficient tab reuse.

Manages a fixed pool of browser pages (tabs) for concurrent scraping.
Pages are reused across domains to avoid creation/destruction overhead.
"""

import asyncio
import sys
from typing import Optional
from playwright.async_api import Page, BrowserContext


class PagePool:
    """
    A pool of reusable browser pages for concurrent scraping.
    
    Usage:
        async with PagePool(context, size=4) as pool:
            page = await pool.acquire()
            try:
                # ... use page ...
            finally:
                await pool.release(page)
    """
    
    def __init__(self, context: BrowserContext, size: int = 4):
        """
        Initialize page pool.
        
        Args:
            context: Playwright browser context
            size: Number of pages to maintain in pool
        """
        self.context = context
        self.size = size
        self._available: asyncio.Queue[Page] = asyncio.Queue()
        self._all_pages: list[Page] = []
        self._initialized = False
    
    async def __aenter__(self) -> "PagePool":
        """Initialize pool and create pages."""
        await self._initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close all pages in pool."""
        await self.close()
    
    async def _initialize(self) -> None:
        """Create initial pages for the pool."""
        if self._initialized:
            return
        
        for i in range(self.size):
            try:
                page = await self.context.new_page()
                self._all_pages.append(page)
                await self._available.put(page)
            except Exception as e:
                sys.stderr.write(f"[POOL] Failed to create page {i}: {e}\n")
        
        self._initialized = True
        sys.stderr.write(f"[POOL] Initialized with {len(self._all_pages)} pages\n")
    
    async def acquire(self, timeout: float = 30.0) -> Page:
        """
        Acquire a page from the pool.
        
        Blocks until a page is available or timeout is reached.
        
        Args:
            timeout: Max seconds to wait for a page
            
        Returns:
            A Page instance ready for use
            
        Raises:
            asyncio.TimeoutError if no page available within timeout
        """
        try:
            page = await asyncio.wait_for(
                self._available.get(),
                timeout=timeout
            )
            return page
        except asyncio.TimeoutError:
            sys.stderr.write(f"[POOL] Timeout waiting for available page\n")
            raise
    
    async def release(self, page: Page) -> None:
        """
        Release a page back to the pool.
        
        Clears page state before returning it to the pool.
        If page is crashed, creates a replacement.
        
        Args:
            page: The page to release
        """
        try:
            # Check if page is still usable
            if page.is_closed():
                # Page crashed - create replacement
                sys.stderr.write("[POOL] Page crashed, creating replacement\n")
                await self._replace_page(page)
                return
            
            # Clear page state for next domain
            await self._clear_page(page)
            
            # Return to pool
            await self._available.put(page)
            
        except Exception as e:
            sys.stderr.write(f"[POOL] Error releasing page: {e}\n")
            await self._replace_page(page)
    
    async def _clear_page(self, page: Page) -> None:
        """
        Clear page state between domains.
        
        Args:
            page: Page to clear
        """
        try:
            # Navigate to blank page to clear state
            await page.goto("about:blank", timeout=5000)
        except Exception:
            # If goto fails, page might be in bad state
            pass
    
    async def _replace_page(self, old_page: Page) -> None:
        """
        Replace a crashed/broken page with a new one.
        
        Args:
            old_page: The page to replace
        """
        try:
            # Remove old page from tracking
            if old_page in self._all_pages:
                self._all_pages.remove(old_page)
            
            # Close if not already closed
            if not old_page.is_closed():
                await old_page.close()
            
            # Create replacement
            new_page = await self.context.new_page()
            self._all_pages.append(new_page)
            await self._available.put(new_page)
            
        except Exception as e:
            sys.stderr.write(f"[POOL] Failed to replace page: {e}\n")
    
    async def close(self) -> None:
        """Close all pages in the pool."""
        for page in self._all_pages:
            try:
                if not page.is_closed():
                    await page.close()
            except Exception:
                pass
        
        self._all_pages.clear()
        self._initialized = False
    
    @property
    def available_count(self) -> int:
        """Get number of available pages."""
        return self._available.qsize()
    
    @property
    def total_count(self) -> int:
        """Get total number of pages in pool."""
        return len(self._all_pages)
