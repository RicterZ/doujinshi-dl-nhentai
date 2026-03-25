# coding: utf-8
"""
Plugin HTTP helpers.

This module provides request() and async_request() with authentication
headers (Cookie, User-Agent, Referer) injected automatically from the config.
"""
import sys
import re

import httpx
import requests
import urllib3.exceptions

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_headers():
    from doujinshi_dl_nhentai.constant import CONFIG, LOGIN_URL

    headers = {
        'Referer': LOGIN_URL
    }

    user_agent = CONFIG.get('useragent')
    if user_agent and user_agent.strip():
        headers['User-Agent'] = user_agent

    cookie = CONFIG.get('cookie')
    if cookie and cookie.strip():
        headers['Cookie'] = cookie

    return headers


def request(method, url, **kwargs):
    from doujinshi_dl_nhentai.constant import CONFIG

    session = requests.Session()
    session.headers.update(get_headers())

    if not kwargs.get('proxies', None):
        kwargs['proxies'] = {
            'https': CONFIG['proxy'],
            'http': CONFIG['proxy'],
        }

    return getattr(session, method)(url, verify=False, **kwargs)


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


def check_cookie():
    from doujinshi_dl_nhentai.constant import BASE_URL
    from doujinshi_dl.core.logger import logger

    response = request('get', BASE_URL)

    if response.status_code == 403 and 'Just a moment...' in response.text:
        logger.error('Blocked by Cloudflare captcha, please set your cookie and useragent')
        sys.exit(1)

    username = re.findall('"/users/[0-9]+/(.*?)"', response.text)
    if not username:
        logger.warning(
            'Cannot get your username, please check your cookie or use `doujinshi-dl --cookie` to set your cookie')
    else:
        logger.log(16, f'Login successfully! Your username: {username[0]}')
