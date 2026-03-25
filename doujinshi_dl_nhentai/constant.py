# coding: utf-8
import os
import tempfile

from urllib.parse import urlparse
from platform import system


def get_plugin_home() -> str:
    home = os.getenv('HOME', tempfile.gettempdir())

    if system() == 'Linux':
        xdgdat = os.getenv('XDG_DATA_HOME')
        if xdgdat and os.path.exists(os.path.join(xdgdat, 'doujinshi-dl')):
            return os.path.join(xdgdat, 'doujinshi-dl')
        # Legacy path migration: keep using ~/.nhentai if it already exists
        if home and os.path.exists(os.path.join(home, '.nhentai')):
            return os.path.join(home, '.nhentai')
        if xdgdat:
            return os.path.join(xdgdat, 'doujinshi-dl')

    # Legacy path migration: keep using ~/.nhentai if it already exists
    if home and os.path.exists(os.path.join(home, '.nhentai')):
        return os.path.join(home, '.nhentai')
    return os.path.join(home, '.doujinshi-dl')


# Keep old name as alias for backwards compatibility
get_nhentai_home = get_plugin_home


DEBUG = os.getenv('DEBUG', False)
BASE_URL = os.getenv('DOUJINSHI_DL_URL', 'https://nhentai.net')

DETAIL_URL = f'{BASE_URL}/g'
LEGACY_SEARCH_URL = f'{BASE_URL}/search/'
SEARCH_URL = f'{BASE_URL}/api/galleries/search'
ARTIST_URL = f'{BASE_URL}/artist/'

TAG_API_URL = f'{BASE_URL}/api/galleries/tagged'
LOGIN_URL = f'{BASE_URL}/login/'
CHALLENGE_URL = f'{BASE_URL}/challenge'
FAV_URL = f'{BASE_URL}/favorites/'

PATH_SEPARATOR = os.path.sep

RETRY_TIMES = 3


IMAGE_URL = f'{urlparse(BASE_URL).scheme}://i1.{urlparse(BASE_URL).hostname}/galleries'
IMAGE_URL_MIRRORS = [
    f'{urlparse(BASE_URL).scheme}://i2.{urlparse(BASE_URL).hostname}',
    f'{urlparse(BASE_URL).scheme}://i3.{urlparse(BASE_URL).hostname}',
    f'{urlparse(BASE_URL).scheme}://i4.{urlparse(BASE_URL).hostname}',
    f'{urlparse(BASE_URL).scheme}://i5.{urlparse(BASE_URL).hostname}',
    f'{urlparse(BASE_URL).scheme}://i6.{urlparse(BASE_URL).hostname}',
    f'{urlparse(BASE_URL).scheme}://i7.{urlparse(BASE_URL).hostname}',
]

NHENTAI_HOME = get_plugin_home()
NHENTAI_HISTORY = os.path.join(NHENTAI_HOME, 'history.sqlite3')
NHENTAI_CONFIG_FILE = os.path.join(NHENTAI_HOME, 'config.json')

# Generic aliases — preferred names for plugin-agnostic code
PLUGIN_HOME = NHENTAI_HOME
PLUGIN_HISTORY = NHENTAI_HISTORY
PLUGIN_CONFIG_FILE = NHENTAI_CONFIG_FILE

__api_suspended_DETAIL_URL = f'{BASE_URL}/api/gallery'

CONFIG = {
    'proxy': '',
    'cookie': '',
    'language': '',
    'template': '',
    'useragent': 'doujinshi-dl (https://github.com/RicterZ/doujinshi-dl)',
    'max_filename': 85
}

LANGUAGE_ISO = {
    'english': 'en',
    'chinese': 'zh',
    'japanese': 'ja',
    'translated': 'translated'
}
