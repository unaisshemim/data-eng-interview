# Logo Crawler

A high-performance, two-phase logo extraction tool that crawls websites to extract their logo URLs. The system uses a hybrid approach: fast static HTTP scraping first, then Playwright browser rendering for JavaScript-heavy sites.

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
cat websites.csv | python -m py.logocrawler.logo_crawler > results.csv
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

The crawler operates in two phases:

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

---

## Performance Analytics

| Metric                    | Value           |
| ------------------------- | --------------- |
| **System Resources**      |                 |
| RAM Available             | 5.8 GB          |
| CPUs                      | 10              |
| Static Workers            | 37              |
| Playwright Workers        | 8               |
| **Crawl Statistics**      |                 |
| Total Domains Crawled     | 50              |
| Found (Static)            | 30 (60%)        |
| Found (Playwright)        | 17 (34%)        |
| **Total Success Rate**    | **94%** (47/50) |
| Failed                    | 3 (6%)          |
| **Timing**                |                 |
| Static Phase Duration     | 43.1s           |
| Playwright Phase Duration | 31.0s           |
| **Total Time**            | ~74s            |
| Static Rate               | 1.16 domains/s  |
| Playwright Rate           | 0.65 domains/s  |

> **Note:** Performance may vary based on network conditions, target website response times, and system resources.

---

## Project Structure

```
py/logocrawler/
├── logo_crawler.py       # Main entry point
├── config.py             # Configuration constants
├── static/               # Static HTTP scraping
│   ├── http_client.py
│   ├── logo_extractor.py
│   └── processor_async.py
├── playwright/           # Browser-based rendering
│   ├── browser_manager.py
│   └── helpers/
│       ├── cookie_handler.py
│       ├── domain_processor.py
│       ├── logo_extractor.py
│       ├── page_pool.py
│       └── restart_manager.py
└── utils/
    ├── progress.py
    ├── validators.py
    └── worker.py
```

---

## Configuration

Key settings in `config.py`:

| Setting                   | Default | Description                     |
| ------------------------- | ------- | ------------------------------- |
| `MAX_DOMAINS`             | 50      | Limit domains to process        |
| `DEFAULT_TIMEOUT`         | (2, 5)  | Connect/read timeout in seconds |
| `PLAYWRIGHT_TIMEOUT`      | 10000   | Browser timeout in milliseconds |
| `PLAYWRIGHT_TABS`         | 4       | Concurrent browser tabs         |
| `RESTART_EVERY_N_DOMAINS` | 50      | Browser restart interval        |

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
