import sys
import csv
import time
import asyncio
import aiohttp
from .config import HEADERS, MAX_DOMAINS


from .utils.worker import get_optimal_workers, get_playwright_workers
from .utils.csv_writer import IncrementalCSVWriter
from .static.processor_async import process_domain_static
from .utils.progress import print_progress

from .playwright.browser_manager import run_playwright_batch



PROGRESS_UPDATE_INTERVAL = 1


async def run_static_phase(domains, concurrency, writer):
    """Phase 1: Static HTTP scraping with aiohttp."""
    total = len(domains)
    processed = 0
    found = 0
    needs_render = []
    failed_domains = []
    
    start_time = time.time()
    
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
                await writer.write(domain, logo_url)
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
    
    return found, needs_render, failed_domains


async def run_playwright_phase(domains, writer):
    """Phase 2: Playwright rendering for domains that need it."""
    if not domains:
        return 0, []
    
    return await run_playwright_batch(domains, writer)



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

    # Initialize incremental CSV writer
    writer = IncrementalCSVWriter(sys.stdout, buffer_size=10)
    writer.write_header()

    # ----------------------------
    # Phase 1: Static scraping
    # ----------------------------
    sys.stderr.write(f"\n{'='*60}\n")
    sys.stderr.write(f"PHASE 1: Static HTTP Scraping ({static_workers} workers)\n")
    sys.stderr.write(f"{'='*60}\n")

    static_found, needs_render, static_failed = await run_static_phase(domains, static_workers, writer)

    # ----------------------------
    # Phase 2: Playwright rendering
    # ----------------------------
    if needs_render:
        sys.stderr.write(f"\n{'='*60}\n")
        sys.stderr.write(f"PHASE 2: Playwright Rendering ({playwright_workers} workers)\n")
        sys.stderr.write(f"{'='*60}\n")

        playwright_found, playwright_failed = await run_playwright_phase(needs_render, writer)
    else:
        playwright_found = 0
        playwright_failed = []
        sys.stderr.write("\n[SKIP] No domains need rendering - all found in static phase!\n")

    # Flush any remaining buffered results
    await writer.close()

    # Combine failed domains
    all_failed = static_failed + playwright_failed
    total_found = static_found + playwright_found

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
    sys.stderr.write(f"Found (static): {static_found}\n")
    sys.stderr.write(f"Found (playwright): {playwright_found}\n")
    sys.stderr.write(f"Total found: {total_found}\n")
    sys.stderr.write(f"Failed: {len(domains) - total_found}\n")


if __name__ == "__main__":
    asyncio.run(main())