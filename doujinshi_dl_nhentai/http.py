# coding: utf-8
"""
Plugin HTTP helpers.

This module provides request() and async_request() with authentication
headers (Authorization / Cookie, User-Agent, Referer) injected automatically
from the config.

Authentication priority: token (API key) > cookie

Rate limiting: A token-bucket limiter caps outgoing requests at 14/min
(under the site's 15/min hard limit). HTTP 429 responses trigger exponential
backoff with automatic retry.
"""
import sys
import time
import threading

import httpx
import requests
import urllib3.exceptions

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class _RateLimiter:
    """Simple token-bucket rate limiter.

    Allows up to `rate` requests per `period` seconds.  Callers block via
    acquire() until a token is available.
    """

    def __init__(self, rate: int = 14, period: float = 60.0):
        self.rate = rate
        self.period = period
        self._lock = threading.Lock()
        self._tokens = float(rate)
        self._last = time.monotonic()

    def acquire(self):
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._tokens = min(self.rate, self._tokens + elapsed * (self.rate / self.period))
            self._last = now

            if self._tokens < 1.0:
                wait = (1.0 - self._tokens) * (self.period / self.rate)
                time.sleep(wait)
                self._tokens = 0.0
                self._last = time.monotonic()
            else:
                self._tokens -= 1.0


_limiter = _RateLimiter(rate=14, period=60.0)
_MAX_429_RETRIES = 5


def get_headers():
    from doujinshi_dl_nhentai.constant import CONFIG

    headers = {}

    user_agent = CONFIG.get('useragent')
    if user_agent and user_agent.strip():
        headers['User-Agent'] = user_agent

    # Priority: token (API key) > cookie (legacy fallback)
    token = CONFIG.get('token', '').strip()
    cookie = CONFIG.get('cookie', '').strip()

    if token:
        headers['Authorization'] = f'Key {token}'
    elif cookie:
        headers['Cookie'] = cookie

    return headers


def request(method, url, **kwargs):
    from doujinshi_dl_nhentai.constant import CONFIG
    from doujinshi_dl.core.logger import logger

    session = requests.Session()
    session.headers.update(get_headers())

    if not kwargs.get('proxies', None):
        kwargs['proxies'] = {
            'https': CONFIG['proxy'],
            'http': CONFIG['proxy'],
        }

    backoff = 2.0
    for attempt in range(_MAX_429_RETRIES + 1):
        _limiter.acquire()
        resp = getattr(session, method)(url, verify=False, **kwargs)

        if resp.status_code != 429:
            return resp

        # Rate-limited — exponential backoff
        if attempt < _MAX_429_RETRIES:
            retry_after = resp.headers.get('Retry-After')
            wait = float(retry_after) if retry_after and retry_after.isdigit() else backoff
            logger.warning(f'Rate limited (429), waiting {wait:.1f}s before retry ({attempt + 1}/{_MAX_429_RETRIES})...')
            time.sleep(wait)
            backoff = min(backoff * 2, 60.0)

    logger.error(f'Still rate-limited after {_MAX_429_RETRIES} retries: {url}')
    return resp


async def async_request(method, url, proxy=None, **kwargs):
    from doujinshi_dl_nhentai.constant import CONFIG

    headers = get_headers()

    if proxy is None:
        proxy = CONFIG.get('proxy', '')

    if isinstance(proxy, str) and not proxy:
        proxy = None

    timeout = kwargs.pop('timeout', 30)

    async with httpx.AsyncClient(headers=headers, verify=False, proxy=proxy,
                                 timeout=timeout) as client:
        response = await client.request(method, url, **kwargs)

    return response


def check_auth():
    from doujinshi_dl_nhentai.constant import V2_USER_URL, V2_FAV_URL
    from doujinshi_dl.core.logger import logger

    # Try User Token endpoint first; falls back to favorites for API Key auth
    response = request('get', V2_USER_URL)

    if response.status_code == 200:
        try:
            data = response.json()
            username = (data.get('username')
                        or data.get('name')
                        or data.get('slug', ''))
        except Exception:
            username = ''
        logger.log(16, f'Login successfully! Your username: {username}')
        return

    if response.status_code == 401:
        # API Key cannot access /user — try /favorites as a secondary check
        fav_resp = request('get', V2_FAV_URL, params={'page': 1})
        if fav_resp.status_code == 200:
            logger.log(16, 'Login successfully! (API Key)')
            return
        logger.warning(
            'Not authenticated. Use --token to set your API token.')
        return

    if response.status_code == 403 and 'Just a moment' in response.text:
        logger.error('Blocked by Cloudflare captcha, please set your cookie and useragent')
        sys.exit(1)

    logger.warning(f'Auth check returned HTTP {response.status_code}')


# Backwards-compatibility alias
check_cookie = check_auth
