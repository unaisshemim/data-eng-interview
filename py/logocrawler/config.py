"""Configuration constants for logo crawler."""

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LogoCrawler/2.0)"
}

# Default timeouts for requests (connect, read)
DEFAULT_TIMEOUT = (2, 5)
HEAD_TIMEOUT = (2, 4)

# Worker constraints
MIN_WORKERS = 10
MAX_WORKERS = 120

# Memory estimation per worker (MB)
MEMORY_PER_WORKER = 120

#Domain Limit 
MAX_DOMAINS = 1000 # add 1000 for full test or use 50 for quick test



# Batch processing and autoscaling
BATCH_SIZE = 200
CPU_LOW_THRESHOLD = 50
CPU_HIGH_THRESHOLD = 90

# Playwright rendering configuration
PLAYWRIGHT_TIMEOUT = 10000  # milliseconds
PLAYWRIGHT_MEMORY_PER_WORKER = 400  # MB per browser instance

# Optimized batch processing settings
MAX_CONCURRENT_TABS = 5  # Maximum tabs open simultaneously
PLAYWRIGHT_TABS = 4  # Number of concurrent browser tabs for scraping
RESTART_EVERY_N_DOMAINS = 50  # Restart browser context every N domains
MEMORY_RESTART_THRESHOLD = 0.75  # Restart browser at 75% memory usage
MEMORY_CHECK_INTERVAL = 10  # Check memory every N domains
GRACEFUL_RESTART_WAIT = 30  # Max seconds to wait for graceful restart
COOKIE_CONSENT_TIMEOUT = 2000  # milliseconds to wait for cookie dialog
ENABLE_SHADOW_DOM = True

# Anti-blocking and rate limiting
DOMAIN_TIMEOUT = 12000  # Hard per-domain timeout in milliseconds
NAV_TIMEOUT = 8000  # Navigation timeout per URL attempt
POST_NAV_DELAY = 800  # Delay after navigation (instead of networkidle)
PAGE_MAX_USES = 25  # Recreate page after N uses
REQUEST_DELAY_MIN = 500  # Minimum delay between requests (ms)
REQUEST_DELAY_MAX = 1500  # Maximum delay between requests (ms)

# User-agent rotation pool
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Viewport rotation pool
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 720},
]

# Common cookie consent button selectors
COOKIE_CONSENT_SELECTORS = [
    'button:has-text("Accept")',
    'button:has-text("Accept all")',
    'button:has-text("Agree")',
    'button:has-text("OK")',
    '[id*="accept"]',
    '[class*="accept"]',
    'button:has-text("Reject")',
    'button:has-text("Reject all")',
]
