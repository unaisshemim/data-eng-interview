"""Logo extraction strategies for Playwright pages.

Extracts logo URLs using multiple strategies:
1. <img> tags with logo-related attributes
2. <link rel="icon"> and <link rel="apple-touch-icon">
3. Inline <svg> elements
4. Background images in CSS

Priority: SVG > PNG > JPG > favicon
"""

from typing import Optional
from playwright.async_api import Page

from ...utils.validators import is_valid_image_url


# JavaScript to extract logo URLs from the page
LOGO_EXTRACTION_JS = """
() => {
    const results = [];
    const seenUrls = new Set();
    
    // Helper to add URL with priority
    function addResult(url, priority, source) {
        if (!url || seenUrls.has(url)) return;
        seenUrls.add(url);
        
        // Make URL absolute
        try {
            url = new URL(url, document.baseURI).href;
        } catch (e) {
            return;
        }
        
        results.push({ url, priority, source });
    }
    
    // Helper to check if text contains logo-related keywords
    function isLogoRelated(text) {
        if (!text) return false;
        const lower = text.toLowerCase();
        return /logo|brand|header|navbar|site-|company/.test(lower);
    }
    
    // Helper to get extension priority (lower is better)
    function getExtPriority(url) {
        const lower = url.toLowerCase();
        if (lower.includes('.svg')) return 0;
        if (lower.includes('.png')) return 1;
        if (lower.includes('.jpg') || lower.includes('.jpeg')) return 2;
        if (lower.includes('.webp')) return 3;
        if (lower.includes('.ico')) return 4;
        if (lower.includes('.gif')) return 5;
        return 6;
    }
    
    // 1. Find <img> tags with logo-related attributes
    const imgs = document.querySelectorAll('img');
    for (const img of imgs) {
        const alt = img.alt || '';
        const className = img.className || '';
        const id = img.id || '';
        const src = img.src || img.dataset?.src || img.dataset?.lazySrc || '';
        
        // Check if any attribute suggests this is a logo
        const attrs = [alt, className, id, src].join(' ');
        if (isLogoRelated(attrs)) {
            const url = img.src || img.dataset?.src || img.dataset?.lazySrc || 
                       img.dataset?.original || img.dataset?.url;
            if (url) {
                const priority = 10 + getExtPriority(url);
                addResult(url, priority, 'img-logo');
            }
        }
    }
    
    // 2. Find <link rel="icon"> and apple-touch-icon
    const iconLinks = document.querySelectorAll(
        'link[rel="icon"], link[rel="shortcut icon"], link[rel="apple-touch-icon"], link[rel="apple-touch-icon-precomposed"]'
    );
    for (const link of iconLinks) {
        const href = link.href;
        if (href) {
            // Apple touch icons are usually high quality
            const isApple = link.rel.includes('apple');
            const priority = isApple ? 25 : 30 + getExtPriority(href);
            addResult(href, priority, 'link-icon');
        }
    }
    
    // 3. Find inline SVG in header/nav areas
    const headerAreas = document.querySelectorAll('header, nav, [class*="header"], [class*="nav"], [class*="logo"]');
    for (const area of headerAreas) {
        const svgs = area.querySelectorAll('svg');
        for (const svg of svgs) {
            // Convert SVG to data URL
            const svgStr = new XMLSerializer().serializeToString(svg);
            if (svgStr.length > 50 && svgStr.length < 50000) {
                const dataUrl = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgStr)));
                addResult(dataUrl, 5, 'inline-svg');
            }
        }
    }
    
    // 4. Check for logo in any img with explicit logo path
    for (const img of imgs) {
        const src = img.src || '';
        if (src && (src.includes('/logo') || src.includes('/brand'))) {
            const priority = 15 + getExtPriority(src);
            addResult(src, priority, 'img-path');
        }
    }
    
    // 5. Check header/nav for any img (fallback)
    for (const area of headerAreas) {
        const areaImgs = area.querySelectorAll('img');
        for (const img of areaImgs) {
            const src = img.src || img.dataset?.src;
            if (src) {
                const priority = 40 + getExtPriority(src);
                addResult(src, priority, 'header-img');
            }
        }
    }
    
    // 6. Background images with logo patterns
    const allElements = document.querySelectorAll('[style*="background"]');
    for (const el of allElements) {
        const style = el.getAttribute('style') || '';
        const match = style.match(/url\\(['"]?([^'"\\)]+)['"]?\\)/i);
        if (match && match[1]) {
            const url = match[1];
            if (isLogoRelated(url) || isLogoRelated(el.className)) {
                const priority = 35 + getExtPriority(url);
                addResult(url, priority, 'bg-image');
            }
        }
    }
    
    // Sort by priority (lower is better) and return top candidates
    results.sort((a, b) => a.priority - b.priority);
    return results.slice(0, 10);
}
"""


async def extract_logo(page: Page) -> str:
    """
    Extract logo URL from page using multiple strategies.
    
    Args:
        page: Playwright page instance
        
    Returns:
        Absolute logo URL or empty string if not found.
    """
    try:
        # Run extraction in browser context
        candidates = await page.evaluate(LOGO_EXTRACTION_JS)
        
        if not candidates:
            return ""
        
        # Filter and validate candidates
        for candidate in candidates:
            url = candidate.get("url", "")
            if not url:
                continue
            
            # Data URLs are always valid
            if url.startswith("data:image/"):
                return url
            
            # Validate image URL
            if is_valid_image_url(url):
                return url
        
        return ""
        
    except Exception:
        return ""


async def extract_favicon(page: Page) -> str:
    """
    Extract favicon URL as fallback.
    
    Args:
        page: Playwright page instance
        
    Returns:
        Favicon URL or empty string.
    """
    try:
        # Try common favicon locations
        favicon_js = """
        () => {
            // Check link tags first
            const iconLink = document.querySelector(
                'link[rel="icon"], link[rel="shortcut icon"]'
            );
            if (iconLink && iconLink.href) {
                return iconLink.href;
            }
            
            // Default favicon.ico
            return new URL('/favicon.ico', document.baseURI).href;
        }
        """
        
        url = await page.evaluate(favicon_js)
        
        if url and is_valid_image_url(url):
            return url
        
        return ""
        
    except Exception:
        return ""
