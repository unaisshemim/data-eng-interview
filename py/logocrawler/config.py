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
PHASE_1_TIMEOUT = 5000  # Initial phase timeout (2 seconds)
PHASE_R1_TIMEOUT = 7000  # Retry phase 1 timeout (3 seconds)
PHASE_R3_TIMEOUT = 9000  # Retry phase 3 timeout (5 seconds)
MEMORY_CHECK_INTERVAL = 10  # Check memory every N domains
GRACEFUL_RESTART_WAIT = 30  # Max seconds to wait for graceful restart
COOKIE_CONSENT_TIMEOUT = 2000  # milliseconds to wait for cookie dialog
ENABLE_SHADOW_DOM = True

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
