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

# v2 API
V2_BASE_URL    = f'{BASE_URL}/api/v2'
V2_GALLERY_URL = f'{V2_BASE_URL}/galleries'
V2_TAGGED_URL  = f'{V2_BASE_URL}/galleries/tagged'
V2_TAGS_URL    = f'{V2_BASE_URL}/tags'
V2_SEARCH_URL  = f'{V2_BASE_URL}/search'
V2_FAV_URL     = f'{V2_BASE_URL}/favorites'
V2_USER_URL    = f'{V2_BASE_URL}/user'

DETAIL_URL = f'{BASE_URL}/g'

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

CONFIG = {
    'proxy': '',
    'cookie': '',
    'token': '',
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
