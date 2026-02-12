from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List
import re

from ..utils.validators import is_valid_image_url


URL_IN_STYLE_RE = re.compile(r'url\((.*?)\)', re.I)


def normalize_url(base_url: str, url: str) -> str:
    url = (url or "").strip()
    url = url.strip('"').strip("'").strip()

    if not url:
        return ""

    # protocol-relative
    if url.startswith("//"):
        parsed = urlparse(base_url)
        url = f"{parsed.scheme}:{url}"

    # data urls keep as-is
    if url.startswith("data:"):
        return url

    return urljoin(base_url, url)


def extract_logo(html: str, base_url: str) -> str:
    """
    Simple interview version:
    - finds first usable logo-like asset
    - supports <img>, inline <svg>, inline background-image
    """

    if not html or not base_url:
        return ""

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return ""

    # 1) <img> tags
    for img in soup.find_all("img"):
        try:
            src = img.get("src") or ""

            # lazy loading
            if not src:
                src = (
                    img.get("data-src")
                    or img.get("data-lazy-src")
                    or img.get("data-original")
                    or img.get("data-url")
                    or ""
                )

            # srcset
            if not src and img.get("srcset"):
                srcset = img.get("srcset", "")
                parts = [p.strip() for p in srcset.split(",") if p.strip()]
                if parts:
                    src = parts[0].split()[0]

            if not src:
                continue

            full_url = normalize_url(base_url, src)

            # allow data:image...
            if full_url.startswith("data:"):
                return full_url

            if is_valid_image_url(full_url):
                return full_url

        except Exception:
            continue

    # 2) background-image in inline styles
    for tag in soup.find_all(style=True):
        try:
            style = tag.get("style") or ""
            if "url(" not in style.lower():
                continue

            matches = URL_IN_STYLE_RE.findall(style)
            for raw in matches:
                raw = (raw or "").strip()
                raw = raw.strip('"').strip("'").strip()

                if not raw:
                    continue

                full_url = normalize_url(base_url, raw)

                if full_url.startswith("data:"):
                    return full_url

                if is_valid_image_url(full_url):
                    return full_url

        except Exception:
            continue

    # 3) inline SVG
    for svg in soup.find_all("svg"):
        try:
            svg_str = str(svg).strip()
            if len(svg_str) < 30:
                continue

            # store as data url
            return "data:image/svg+xml;utf8," + svg_str

        except Exception:
            continue

    return ""
