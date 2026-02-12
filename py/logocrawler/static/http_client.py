import aiohttp
from typing import Optional


async def fetch_html(
    session: aiohttp.ClientSession, 
    url: str, 
    timeout: int = 10
) -> Optional[str]:
    """
    Fetch HTML with error handling.
    
    Args:
        session: aiohttp client session
        url: URL to fetch
        timeout: Request timeout in seconds
    
    Returns:
        HTML content or None if failed
    """
    try:
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        async with session.get(
            url, 
            allow_redirects=True, 
            timeout=timeout_obj,
            headers=headers,
            max_redirects=5
        ) as resp:
            if resp.status >= 400:
                return None
            
            content = await resp.read()
            
            try:
                encoding = resp.charset or 'utf-8'
                html = content.decode(encoding, errors='ignore')
            except (UnicodeDecodeError, LookupError):
                html = content.decode('utf-8', errors='ignore')
            
            if not html or len(html.strip()) < 50:
                return None
            
            return html
            
    except (aiohttp.ClientError, Exception):
        return None
