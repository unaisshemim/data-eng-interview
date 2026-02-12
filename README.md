# Logo Crawler

A high-performance, two-phase logo extraction tool that crawls websites to extract their logo URLs. The system uses a hybrid approach: fast static HTTP scraping first, then Playwright browser rendering for JavaScript-heavy sites.

Includes anti-blocking measures: rate limiting, user-agent rotation, viewport rotation, and captcha detection.

> **Note:** AI tools were used for research and troubleshooting during development. The core architecture and implementation are my own work.

---

## Installation

This project uses [Nix](https://nixos.org/) for reproducible dependency management.

### Prerequisites

- Nix package manager installed on your system
- macOS or Linux

### Setup

```bash
# Enter the development environment
nix-shell

# This automatically:
# - Sets up Python 3 with all dependencies
# - Installs Playwright Firefox browser
```

---

## Usage

```bash
cat websites.csv | python -m py.logocrawler.app > results.csv
```

### Input Format

`websites.csv` should contain one domain per line:

```
example.com
google.com
github.com
```

### Output

Results are written to `results.csv` in the format:

```
domain,logo_url
```

Failed domains are logged to `failed_domains.csv`.

---

## Architecture

The crawler operates in two phases with anti-blocking protection:

### Phase 1: Static HTTP Scraping

- Uses `aiohttp` for async HTTP requests
- Extracts logos from HTML without JavaScript rendering
- Highly concurrent (37+ workers based on system resources)
- Fast: ~1.16 requests/second

### Phase 2: Playwright Rendering

- Falls back to headless Firefox for JS-rendered pages
- Handles cookie consent dialogs automatically
- Uses page pooling for efficiency (4 tabs per browser)
- Processes remaining domains at ~0.65 requests/second

### Anti-Blocking Features

- **Rate limiting**: Random delays (500-1500ms) between requests
- **User-agent rotation**: 7 browser UA strings (Chrome, Firefox, Safari)
- **Viewport rotation**: 5 common screen resolutions
- **Captcha detection**: Detects reCAPTCHA, hCaptcha, Cloudflare challenges
- **Page lifecycle**: Pages recycled after 25 uses to prevent fingerprinting
- **Hard timeout**: 12s per-domain limit prevents stuck tabs

---

## Performance Analytics

| Metric             | Value   |
| ------------------ | ------- |
| Total Domains      | 50      |
| Found (Static)     | 60%     |
| Found (Playwright) | 34%     |
| **Success Rate**   | **94%** |
| Failed             | 6%      |
| Total Time         | ~74s    |

> **Note:** Performance may vary based on network conditions and system resources.

---

## Project Structure

```
py/logocrawler/
├── app.py                # Main entry point
├── config.py             # Configuration constants
├── static/               # Static HTTP scraping
│   ├── http_client.py
│   ├── logo_extractor.py
│   └── processor_async.py
├── playwright/           # Browser-based rendering
│   ├── browser_manager.py
│   └── helpers/
│       ├── anti_blocking.py   # UA/viewport rotation, captcha detection
│       ├── cookie_handler.py
│       ├── domain_processor.py
│       ├── logo_extractor.py
│       ├── page_pool.py
│       └── restart_manager.py
└── utils/
    ├── csv_writer.py
    ├── progress.py
    ├── validators.py
    └── worker.py
```

---

## Configuration

Key settings in `config.py`:

| Setting                   | Default | Description                     |
| ------------------------- | ------- | ------------------------------- |
| `MAX_DOMAINS`             | 1000    | Limit domains to process        |
| `DEFAULT_TIMEOUT`         | (2, 5)  | Connect/read timeout in seconds |
| `PLAYWRIGHT_TABS`         | 4       | Concurrent browser tabs         |
| `RESTART_EVERY_N_DOMAINS` | 50      | Context restart interval        |
| `DOMAIN_TIMEOUT`          | 12000   | Hard per-domain timeout (ms)    |
| `NAV_TIMEOUT`             | 8000    | Navigation timeout per URL (ms) |
| `PAGE_MAX_USES`           | 25      | Page lifecycle limit            |
| `REQUEST_DELAY_MIN`       | 500     | Min delay between requests (ms) |
| `REQUEST_DELAY_MAX`       | 1500    | Max delay between requests (ms) |

---

## Dependencies

Managed via Nix (`default.nix`):

- Python 3
- aiohttp
- beautifulsoup4
- playwright
- requests
- psutil

---

## License

MIT
