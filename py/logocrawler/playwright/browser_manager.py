"""Browser manager for batch Playwright processing.

Orchestrates:
- Single Firefox browser instance
- Browser context lifecycle
- Page pool management
- Restart logic for memory efficiency
- Anti-blocking: rate limiting, UA/viewport rotation
"""

import sys
import time
import asyncio
from typing import List, Tuple
from playwright.async_api import async_playwright

from ..config import PLAYWRIGHT_TABS, DOMAIN_TIMEOUT
from ..utils.progress import print_progress
from .helpers.page_pool import PagePool
from .helpers.domain_processor import process_domain
from .helpers.restart_manager import RestartManager
from .helpers.anti_blocking import (
    get_random_user_agent,
    get_random_viewport,
    random_delay,
)


PROGRESS_UPDATE_INTERVAL = 1


def _create_context_options() -> dict:
    """Generate randomized context options for anti-blocking."""
    return {
        "viewport": get_random_viewport(),
        "user_agent": get_random_user_agent(),
    }


async def run_playwright_batch(
    domains: List[str],
    writer,
) -> Tuple[int, List[str]]:
   
    if not domains:
        return 0, []
    
    failed_domains: List[str] = []
    
    total = len(domains)
    processed = 0
    found = 0
    
    start_time = time.time()
    
    # Use configured tab count
    tab_count = PLAYWRIGHT_TABS
    
    # Hard per-domain timeout in seconds
    domain_timeout_sec = DOMAIN_TIMEOUT / 1000
    
    async with async_playwright() as p:
        # Launch Firefox browser (kept alive throughout batch)
        browser = await p.firefox.launch(
            headless=False,
        )
        
        sys.stderr.write(f"[PW] Firefox launched, {tab_count} tabs\n")
        
        # Create context with randomized UA/viewport
        context = await browser.new_context(**_create_context_options())
        
        restart_manager = RestartManager()
        
        async with PagePool(context, size=tab_count) as pool:
            # Semaphore to limit concurrent processing
            sem = asyncio.Semaphore(tab_count)
            
            async def process_one(domain: str) -> Tuple[str, str, bool]:
                """Process single domain with rate limiting and hard timeout."""
                # Rate limiting: random delay before starting
                await random_delay()
                
                async with sem:
                    page = await pool.acquire()
                    try:
                        # Hard per-domain timeout wrapper
                        result = await asyncio.wait_for(
                            process_domain(page, domain),
                            timeout=domain_timeout_sec
                        )
                        return (result[0], result[1], bool(result[1]))
                    except asyncio.TimeoutError:
                        sys.stderr.write(f"[PW] Hard timeout ({DOMAIN_TIMEOUT}ms): {domain}\n")
                        return (domain, "", False)
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
                    await writer.write(domain, logo)
                else:
                    failed_domains.append(domain)
                
                # Progress update
                if processed % PROGRESS_UPDATE_INTERVAL == 0 or processed == total:
                    print_progress(
                        processed, total, found, 0, 0,
                        start_time, tab_count
                    )
                
                # Check if context restart needed (browser stays alive)
                if restart_manager.should_restart() and processed < total:
                    # Close old context
                    old_context = context
                    
                    # Create new context with randomized options
                    context = await browser.new_context(**_create_context_options())
                    
                    # Rebuild pool with new context
                    await pool.rebuild(context)
                    
                    # Now safe to close old context
                    await old_context.close()
                    
                    restart_manager.record_restart()
                    sys.stderr.write(f"[PW] Context restarted (browser kept alive)\n")
        
        # Cleanup
        await context.close()
        await browser.close()
    
    elapsed = time.time() - start_time
    sys.stderr.write(
        f"\n[PW] Done in {elapsed:.1f}s | "
        f"found={found} failed={len(failed_domains)}\n"
    )
    
    return found, failed_domains
