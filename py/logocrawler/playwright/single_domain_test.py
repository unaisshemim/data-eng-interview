import asyncio
from playwright.async_api import async_playwright
from .helpers.domain_processor import process_domain_playwright
import sys


async def main():
    domain = sys.argv[1] if len(sys.argv) > 1 else "shopify.com"

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, args=['--no-sandbox'])
        result = await process_domain_playwright(browser, domain)
        print(f"Domain: {result[0]}")
        print(f"Logo URL: {result[1] or 'Not found'}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
