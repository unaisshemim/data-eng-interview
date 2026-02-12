

import sys
import csv
import time
import asyncio
import aiohttp
from .config import HEADERS,MAX_DOMAINS


from .utils.worker import get_optimal_workers, get_playwright_workers
from .static.processor_async import process_domain_static
from .utils.progress import print_progress

from .playwright.browser_manager import run_playwright_batch



PROGRESS_UPDATE_INTERVAL = 1


async def run_static_phase(domains, concurrency):
    """Phase 1: Static HTTP scraping with aiohttp."""
    total = len(domains)
    processed = 0
    found = 0
    needs_render = []
    failed_domains = []
    
    start_time = time.time()
    
    results = []
    
    sem = asyncio.Semaphore(concurrency)
    
    timeout = aiohttp.ClientTimeout(
        total=10,      # full request
        connect=4,     # TCP connect timeout
        sock_read=6,   # server read timeout
    )
    
    # Reuse ONE session for ALL domains
    connector = aiohttp.TCPConnector(
        limit=concurrency,          # max open connections
        ttl_dns_cache=300,          # cache DNS results
        enable_cleanup_closed=True,
    )
    
    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=HEADERS,
        connector=connector,
    ) as session:
        
        async def sem_task(domain):
            async with sem:
                return await process_domain_static(session, domain)
        
        tasks = [asyncio.create_task(sem_task(d)) for d in domains]
        
        for task in asyncio.as_completed(tasks):
            domain, logo_url, needs_pw = await task
            
            processed += 1
            
            if logo_url:
                found += 1
                results.append((domain, logo_url))
            else:
                if needs_pw:
                    needs_render.append(domain)
                else:
                    failed_domains.append(domain)
            
            if processed % PROGRESS_UPDATE_INTERVAL == 0 or processed == total:
                print_progress(
                    processed, total, found, len(needs_render), 0,
                    start_time, concurrency
                )
    
    elapsed = time.time() - start_time
    sys.stderr.write(f"\n[STATIC PHASE] Done in {elapsed:.1f}s | ")
    sys.stderr.write(f"found={found} needs_render={len(needs_render)} failed={len(failed_domains)}\n")
    
    return results, needs_render, failed_domains


async def run_playwright_phase(domains, concurrency):
    """Phase 2: Playwright rendering for domains that need it."""
    if not domains:
        return [], []
    
    return await run_playwright_batch(domains, concurrency)



async def main():
    # Worker config
    static_workers, memory_gb, cpu_count = get_optimal_workers()
    playwright_workers = get_playwright_workers()

    sys.stderr.write(f"\n{'='*60}\n")
    sys.stderr.write("SYSTEM INFO\n")
    sys.stderr.write(f"{'='*60}\n")
    sys.stderr.write(f"RAM: {memory_gb:.1f}GB available\n")
    sys.stderr.write(f"CPUs: {cpu_count}\n")
    sys.stderr.write(f"Static workers: {static_workers}\n")
    sys.stderr.write(f"Playwright workers: {playwright_workers}\n")

    # Read domains from stdin
    domains = []
    for line in sys.stdin:
        d = line.strip()
        if d:
            domains.append(d)

    original_total = len(domains)

    # Limit domains for testing
    domains = domains[:MAX_DOMAINS]

    sys.stderr.write(f"\nDomains received: {original_total}\n")
    sys.stderr.write(f"Domains to crawl (after limit): {len(domains)}\n")

    # ----------------------------
    # Phase 1: Static scraping
    # ----------------------------
    sys.stderr.write(f"\n{'='*60}\n")
    sys.stderr.write(f"PHASE 1: Static HTTP Scraping ({static_workers} workers)\n")
    sys.stderr.write(f"{'='*60}\n")

    static_results, needs_render, static_failed = await run_static_phase(domains, static_workers)

    # ----------------------------
    # Phase 2: Playwright rendering
    # ----------------------------
    if needs_render:
        sys.stderr.write(f"\n{'='*60}\n")
        sys.stderr.write(f"PHASE 2: Playwright Rendering ({playwright_workers} workers)\n")
        sys.stderr.write(f"{'='*60}\n")

        playwright_results, playwright_failed = await run_playwright_phase(needs_render, playwright_workers)
    else:
        playwright_results = []
        playwright_failed = []
        sys.stderr.write("\n[SKIP] No domains need rendering - all found in static phase!\n")

    # ----------------------------
    # Combine results
    # ----------------------------
    all_results = static_results + playwright_results
    all_failed = static_failed + playwright_failed

    # Output successful results to stdout
    writer = csv.writer(sys.stdout)
    writer.writerow(["domain", "logo_url"])
    for domain, logo in all_results:
        writer.writerow([domain, logo])

    # Write failed domains to CSV file
    if all_failed:
        with open("failed_domains.csv", "w", newline="") as f:
            failed_writer = csv.writer(f)
            failed_writer.writerow(["domain", "reason"])
            for domain in all_failed:
                failed_writer.writerow([domain, "logo_not_found"])
        sys.stderr.write("\nFailed domains written to: failed_domains.csv\n")

    # ----------------------------
    # Final statistics
    # ----------------------------
    sys.stderr.write(f"\n{'='*60}\n")
    sys.stderr.write("FINAL RESULTS\n")
    sys.stderr.write(f"{'='*60}\n")
    sys.stderr.write(f"Total crawled: {len(domains)}\n")
    sys.stderr.write(f"Found (static): {len(static_results)}\n")
    sys.stderr.write(f"Found (playwright): {len(playwright_results)}\n")
    sys.stderr.write(f"Total found: {len(all_results)}\n")
    sys.stderr.write(f"Failed: {len(domains) - len(all_results)}\n")


if __name__ == "__main__":
    asyncio.run(main())