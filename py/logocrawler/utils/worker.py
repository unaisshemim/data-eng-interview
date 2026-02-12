import psutil
from ..config import MIN_WORKERS, MAX_WORKERS, MEMORY_PER_WORKER,PLAYWRIGHT_MEMORY_PER_WORKER


def get_optimal_workers():
    """Calculate optimal number of workers based on available RAM and CPU."""
    memory_gb = psutil.virtual_memory().available / (1024 ** 3)
    cpu_count = psutil.cpu_count(logical=True) or 4

    # For I/O bound crawling: 2x CPU is reasonable baseline
    cpu_based_workers = cpu_count * 4

    # Rough memory estimate per worker
    memory_based_workers = int((memory_gb * 0.75) * 1024 / MEMORY_PER_WORKER)

    workers = min(cpu_based_workers, memory_based_workers)
    workers = max(MIN_WORKERS, min(workers, MAX_WORKERS))
    return workers, memory_gb, cpu_count


def get_playwright_workers():
    """Calculate optimal number of Playwright browser workers.
    
    Browsers use significantly more memory (~400MB each) so we're more conservative.
    """
    
    memory_gb = psutil.virtual_memory().available / (1024 ** 3)
    cpu_count = psutil.cpu_count(logical=True) or 4

    # Browsers are CPU intensive - use CPU count as baseline
    cpu_based_workers = max(2, cpu_count)

    # Conservative memory estimate for browsers
    memory_based_workers = int((memory_gb * 0.6) * 1024 / PLAYWRIGHT_MEMORY_PER_WORKER)

    # Take minimum and clamp to reasonable range
    workers = min(cpu_based_workers, memory_based_workers)
    workers = max(2, min(workers, 20))  # 2-20 browser workers
    
    return workers




