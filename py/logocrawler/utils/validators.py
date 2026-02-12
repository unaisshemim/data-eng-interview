import re
from urllib.parse import urlparse
from typing import Optional


def is_valid_image_url(url: str) -> bool:
    """Validate if URL looks like a valid image."""
    if not url or not url.strip():
        return False
    
    url = url.strip()
    
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.scheme not in ['http', 'https', 'data']:
            return False
    except Exception:
        return False
    
    url_lower = url.lower()
    url_path = parsed.path.lower() if parsed.path else url_lower
    
    # Check for common image extensions
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.bmp', '.avif', '.apng']
    has_extension = any(url_path.endswith(ext) for ext in image_extensions)
    
    is_data_url = url.startswith('data:image/')
    looks_like_image = has_extension or is_data_url or '/logo' in url_path or '/icon' in url_path
    
    # Filter out obvious non-images
    exclude_patterns = ['avatar', 'placeholder', 'blank', 'spacer', 'pixel', 'tracking', '1x1', 'transparent']
    has_exclude = any(pattern in url_lower for pattern in exclude_patterns)
    
    if len(url) > 2048:
        return False
    
    return looks_like_image and not has_exclude


def sanitize_domain(domain: str) -> Optional[str]:
    """
    Sanitize and validate domain input.
    
    Returns: Cleaned domain or None if invalid
    """
    if not domain or not isinstance(domain, str):
        return None
    
    domain = domain.strip().lower()
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.rstrip('/')
    domain = domain.split('/')[0]
    domain = domain.split(':')[0]
    
    if not domain:
        return None
    
    # Validate format
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-_.]*\.[a-zA-Z]{2,}$', domain):
        return None
    
    # Check for invalid TLDs
    invalid_tlds = ['local', 'localhost', 'test', 'invalid', 'example']
    tld = domain.split('.')[-1]
    if tld in invalid_tlds:
        return None
    
    return domain
