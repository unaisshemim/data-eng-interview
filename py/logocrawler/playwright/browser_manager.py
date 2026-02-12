"""Browser manager for batch Playwright processing.

Orchestrates:
- Single Firefox browser instance
- Browser context lifecycle
- Page pool management
- Restart logic for memory efficiency
"""

import sys
import time
import asyncio
from typing import List, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext

from ..config import PLAYWRIGHT_TABS, PLAYWRIGHT_TIMEOUT
from ..utils.progress import print_progress
from .helpers.page_pool import PagePool
from .helpers.domain_processor import process_domain
from .helpers.restart_manager import RestartManager


PROGRESS_UPDATE_INTERVAL = 1


async def run_playwright_batch(
    domains: List[str],
    concurrency: int
) -> Tuple[List[Tuple[str, str]], List[str]]:
    """
    Process domains using Playwright with Firefox.
    
    Args:
        domains: List of domain strings to process
        concurrency: Number of parallel workers (used for worker count, not tabs)
        
    Returns:
        Tuple of (results, failed_domains):
        - results: List of (domain, logo_url) tuples
        - failed_domains: List of domain strings that failed
    """
    if not domains:
        return [], []
    
    results: List[Tuple[str, str]] = []
    failed_domains: List[str] = []
    
    total = len(domains)
    processed = 0
    found = 0
    
    start_time = time.time()
    
    # Use configured tab count
    tab_count = PLAYWRIGHT_TABS
    
    async with async_playwright() as p:
        # Launch Firefox browser
        browser = await p.firefox.launch(
            headless=True,
            args=["--no-sandbox"]
        )
        
        sys.stderr.write(f"[PW] Firefox launched, {tab_count} tabs\n")
        
        # Create context and page pool
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (compatible; LogoCrawler/2.0)"
        )
        
        restart_manager = RestartManager()
        
        async with PagePool(context, size=tab_count) as pool:
            # Semaphore to limit concurrent processing
            sem = asyncio.Semaphore(tab_count)
            
            async def process_one(domain: str) -> Tuple[str, str, bool]:
                """Process single domain, returns (domain, logo, success)."""
                async with sem:
                    page = await pool.acquire()
                    try:
                        result = await process_domain(page, domain)
                        return (result[0], result[1], bool(result[1]))
                    except Exception as e:
                        sys.stderr.write(f"[PW] Error processing {domain}: {e}\n")
                        return (domain, "", False)
                    finally:
                        await pool.release(page)
            
            # Process domains concurrently
            tasks = [asyncio.create_task(process_one(d)) for d in domains]
            
            for task in asyncio.as_completed(tasks):
                domain, logo, success = await task
                
                processed += 1
                restart_manager.increment()
                
                if success and logo:
                    found += 1
                    results.append((domain, logo))
                else:
                    failed_domains.append(domain)
                
                # Progress update
                if processed % PROGRESS_UPDATE_INTERVAL == 0 or processed == total:
                    print_progress(
                        processed, total, found, 0, 0,
                        start_time, tab_count
                    )
                
                # Check if restart needed
                if restart_manager.should_restart() and processed < total:
                    # Close current pool and context
                    await pool.close()
                    await context.close()
                    
                    # Create new context and reinitialize pool
                    context = await browser.new_context(
                        viewport={"width": 1280, "height": 720},
                        user_agent="Mozilla/5.0 (compatible; LogoCrawler/2.0)"
                    )
                    pool.context = context
                    await pool._initialize()
                    
                    restart_manager.record_restart()
        
        # Cleanup
        await context.close()
        await browser.close()
    
    elapsed = time.time() - start_time
    sys.stderr.write(
        f"\n[PW] Done in {elapsed:.1f}s | "
        f"found={found} failed={len(failed_domains)}\n"
    )
    
    return results, failed_domains
