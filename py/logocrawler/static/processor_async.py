import asyncio
import aiohttp
from typing import Tuple, List, Dict
import logging

from .http_client import fetch_html
from .logo_extractor import extract_logo
from ..utils.validators import sanitize_domain

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_domain_static(
    session: aiohttp.ClientSession, 
    domain: str,
    timeout: int = 10
) -> Tuple[str, str, bool]:
    """
    Attempt static scraping of domain.
    
    Args:
        session: aiohttp client session
        domain: Domain to process
        timeout: Request timeout in seconds
    
    Returns:
        (domain, logo_url, needs_render)
        where needs_render=True if no logo found (needs Playwright)
    """
    original_domain = domain
    domain = sanitize_domain(domain)
    
    if not domain:
        return (original_domain, "", False)
    
    # Try multiple URL variations with priority order
    candidates = [
        f"https://{domain}",
        f"https://www.{domain}",
        f"http://{domain}",
        f"http://www.{domain}",
    ]
    
    for base_url in candidates:
        try:
            html = await fetch_html(session, base_url, timeout=timeout)
            
            if not html:
                continue

            logo_url = extract_logo(html, base_url)

            if logo_url:
                return (domain, logo_url, False)

            # HTML loaded but no logo found - might need rendering
            return (domain, "", True)
            
        except Exception:
            continue

    # All attempts failed - needs rendering
    return (domain, "", True)


async def process_domains_batch(
    domains: List[str],
    max_concurrent: int = 10,
    timeout: int = 10,
    connector_limit: int = 100
) -> List[Tuple[str, str, bool]]:
    """
    Process multiple domains concurrently with rate limiting.
    
    Args:
        domains: List of domains to process
        max_concurrent: Maximum concurrent requests
        timeout: Request timeout per domain
        connector_limit: Max connections in connector pool
    
    Returns:
        List of (domain, logo_url, needs_render) tuples
    """
    unique_domains = list(dict.fromkeys(domains))
    
    connector = aiohttp.TCPConnector(
        limit=connector_limit,
        limit_per_host=10,
        ttl_dns_cache=300,
        ssl=False  # Most sites work fine without strict SSL verification for logo scraping
    )
    
    timeout_obj = aiohttp.ClientTimeout(total=timeout * 2)
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout_obj,
        auto_decompress=True,
        trust_env=True
    ) as session:
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(domain):
            async with semaphore:
                return await process_domain_static(session, domain, timeout=timeout)
        
        tasks = [process_with_semaphore(domain) for domain in unique_domains]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                valid_results.append((unique_domains[i], "", True))
            else:
                valid_results.append(result)
        
        return valid_results


def validate_batch_results(results: List[Tuple[str, str, bool]]) -> Dict[str, int]:
    """
    Validate and summarize batch results.
    
    Returns: Dictionary with status counts
    """
    summary = {
        "total": len(results),
        "found_static": 0,
        "needs_render": 0,
        "has_logo": 0,
    }
    
    for domain, logo, needs_render in results:
        if logo:
            summary["found_static"] += 1
        if needs_render:
            summary["needs_render"] += 1
        if logo:
            summary["has_logo"] += 1
    
    return summary


async def process_domains_with_retry(
    domains: List[str],
    max_concurrent: int = 10,
    timeout: int = 10,
    max_retries: int = 2
) -> List[Tuple[str, str, bool]]:
    """
    Process domains with automatic retry for failures.
    
    Args:
        domains: List of domains to process
        max_concurrent: Maximum concurrent requests
        timeout: Request timeout per domain
        max_retries: Maximum retry attempts for failed domains
    
    Returns:
        List of (domain, logo_url, needs_render) tuples
    """
    results = await process_domains_batch(domains, max_concurrent, timeout)
    
    # Find domains that need retry (failed to fetch HTML)
    retry_domains = [
        domain for domain, logo, needs_render in results
        if needs_render and not logo
    ]
    
    retry_count = 0
    while retry_domains and retry_count < max_retries:
        retry_count += 1
        
        # Exponential backoff
        await asyncio.sleep(2 ** retry_count)
        
        # Retry with reduced concurrency
        retry_results = await process_domains_batch(
            retry_domains,
            max_concurrent=max(1, max_concurrent // 2),
            timeout=timeout + 5
        )
        
        # Merge results
        retry_dict = {r[0]: r for r in retry_results}
        results = [
            retry_dict.get(r[0], r) if r[0] in retry_dict else r
            for r in results
        ]
        
        # Update retry list
        retry_domains = [
            domain for domain, logo, needs_render in results
            if needs_render and not logo
        ]
    
    return results
