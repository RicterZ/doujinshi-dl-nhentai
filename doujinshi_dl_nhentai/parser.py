# coding: utf-8
import os
import re
import shutil
import time
from tabulate import tabulate

import doujinshi_dl_nhentai.constant as constant
from doujinshi_dl_nhentai.http import request
from doujinshi_dl.core.logger import logger


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_ext(path):
    """Extract file extension from a gallery page path.

    Handles both normal paths (/galleries/123/1.jpg) and thumbnail paths
    (/galleries/123/1t.jpg) by stripping the trailing 't' before the dot.
    """
    base = os.path.basename(path)
    # strip thumbnail suffix: '1t.jpg' → '1.jpg'
    base = re.sub(r't(\.\w+)$', r'\1', base)
    parts = base.split('.')
    return parts[-1] if len(parts) > 1 else 'jpg'


def _map_sorting(sorting):
    """Map legacy sort parameter names to v2 API accepted values."""
    mapping = {
        'recent': 'date',
        'date': 'date',
        'popular': 'popular',
        'popular-today': 'popular-today',
        'popular-week': 'popular-week',
        'popular-month': 'popular-month',
    }
    return mapping.get(sorting, 'date')

def _parse_tag_to_slug(tag_name):
    """Map tag name to its url slug representation."""
    return tag_name.strip().lower().replace(' | ', '-').replace(' ', '-')


# ---------------------------------------------------------------------------
# v2 API parsers (default)
# ---------------------------------------------------------------------------

def doujinshi_parser(id_, counter=0):
    if not isinstance(id_, (int,)) and (isinstance(id_, (str,)) and not id_.isdigit()):
        raise Exception(f'Doujinshi id({id_}) is not valid')

    id_ = int(id_)
    logger.info(f'Fetching doujinshi information of id {id_}')

    url = f'{constant.V2_GALLERY_URL}/{id_}'
    try:
        response = request('get', url, params={'include': 'pages'})
        if response.status_code == 404:
            logger.error(f'Doujinshi with id {id_} cannot be found')
            return []
        elif response.status_code != 200:
            counter += 1
            if counter >= 10:
                logger.critical(f'Failed to fetch doujinshi information of id {id_}')
                return None
            logger.debug(f'Slow down and retry ({id_}) ...')
            time.sleep(1)
            return doujinshi_parser(str(id_), counter)
    except Exception as e:
        logger.warning(f'Error: {e}, ignored')
        return None

    try:
        data = response.json()
    except Exception as e:
        logger.warning(f'Failed to parse JSON response: {e}')
        return None

    title_obj = data.get('title', {})

    # Group tags by type
    tag_groups = {}
    for tag in data.get('tags', []):
        tag_type = tag.get('type', '').lower()
        tag_groups.setdefault(tag_type, []).append(tag.get('name', ''))

    doujinshi = {
        'id':              data['id'],
        'name':            title_obj.get('english') or title_obj.get('pretty', ''),
        'pretty_name':     title_obj.get('pretty', ''),
        'subtitle':        title_obj.get('japanese', ''),
        'img_id':          str(data['media_id']),
        'pages':           data['num_pages'],
        'favorite_counts': data.get('num_favorites', 0),
        'artists':         ', '.join(tag_groups.get('artist', [])),
        'groups':          ', '.join(tag_groups.get('group', [])),
        'parodies':        ', '.join(tag_groups.get('parody', [])),
        'characters':      ', '.join(tag_groups.get('character', [])),
        'tags':            ', '.join(tag_groups.get('tag', [])),
        'languages':       ', '.join(tag_groups.get('language', [])),
        'categories':      ', '.join(tag_groups.get('category', [])),
        'date':            str(data.get('upload_date', '')),
    }

    # Extract per-page extensions from pages[] array
    pages_data = data.get('pages', [])
    if pages_data:
        doujinshi['ext'] = [_extract_ext(p['path']) for p in pages_data]
    else:
        # Fallback: infer extension from cover path, apply uniformly
        cover_path = data.get('cover', {}).get('path', '')
        ext = _extract_ext(cover_path) if cover_path else 'jpg'
        doujinshi['ext'] = [ext] * data['num_pages']

    return doujinshi


def artist_parser(artist_name, sorting, page, is_page_all=False):
    """Exact artist lookup via tag slug → tagged galleries endpoint."""
    slug = _parse_tag_to_slug(artist_name)
    logger.info(f'Looking up artist tag "{slug}"')

    try:
        resp = request('get', f'{constant.V2_TAGS_URL}/artist/{slug}')
        if resp.status_code == 404:
            logger.warning(f'Artist "{artist_name}" not found, falling back to search')
            return search_parser(f'artist:{artist_name}', sorting, page, is_page_all)
        tag_data = resp.json()
    except Exception as e:
        logger.warning(f'Failed to lookup artist tag: {e}, falling back to search')
        return search_parser(f'artist:{artist_name}', sorting, page, is_page_all)

    tag_id = tag_data.get('id')
    if not tag_id:
        logger.warning(f'No tag id for artist "{artist_name}", falling back to search')
        return search_parser(f'artist:{artist_name}', sorting, page, is_page_all)

    logger.info(f'Found artist tag id {tag_id} for "{artist_name}"')

    result = []
    params = {'tag_id': tag_id, 'sort': _map_sorting(sorting)}

    if not page:
        page = [1]

    if is_page_all:
        logger.info(f'Fetching all pages for artist "{artist_name}"')
        try:
            init_response = request('get', constant.V2_TAGGED_URL,
                                    params={**params, 'page': 1}).json()
        except Exception as e:
            logger.critical(f'Failed to parse tagged response: {e}')
            return result
        page = range(1, init_response.get('num_pages', 1) + 1)

    total = f'/{page[-1]}' if is_page_all else ''
    for p in page:
        logger.info(f'Fetching artist "{artist_name}" galleries on page {p}{total}')
        try:
            resp = request('get', constant.V2_TAGGED_URL,
                           params={**params, 'page': p})
            response = resp.json()
        except Exception as e:
            logger.critical(f'Failed to parse tagged response on page {p}: {e}')
            continue

        if not response or 'result' not in response:
            logger.warning(f'No result in response on page {p}')
            continue

        for row in response['result']:
            title = (row.get('english_title')
                     or row.get('title', {}).get('english', '')
                     or '')
            max_len = constant.CONFIG['max_filename']
            title = title[:max_len] + '..' if len(title) > max_len else title
            result.append({'id': row['id'], 'title': title})

    if not result:
        logger.warning(f'No results for artist "{artist_name}"')

    return result


def search_parser(keyword, sorting, page, is_page_all=False):
    result = []
    params = {'query': keyword, 'sort': _map_sorting(sorting)}

    if not page:
        page = [1]

    if is_page_all:
        logger.info(f'Searching all pages for keyword "{keyword}"')
        try:
            init_response = request('get', constant.V2_SEARCH_URL,
                                    params={**params, 'page': 1}).json()
        except Exception as e:
            logger.critical(f'Failed to parse search response: {e}')
            return result
        page = range(1, init_response.get('num_pages', 1) + 1)

    total = f'/{page[-1]}' if is_page_all else ''
    for p in page:
        logger.info(f'Searching doujinshis using keywords "{keyword}" on page {p}{total}')
        try:
            resp = request('get', constant.V2_SEARCH_URL,
                           params={**params, 'page': p})
            response = resp.json()
        except Exception as e:
            logger.critical(f'Failed to parse search response on page {p}: {e}')
            continue

        if constant.DEBUG:
            logger.debug(f'Response: {response}')

        if not response or 'result' not in response:
            logger.warning(f'No result in response on page {p}')
            continue

        for row in response['result']:
            title = (row.get('english_title')
                     or row.get('title', {}).get('english', '')
                     or '')
            max_len = constant.CONFIG['max_filename']
            title = title[:max_len] + '..' if len(title) > max_len else title
            result.append({'id': row['id'], 'title': title})

    if not result:
        logger.warning(f'No results for keyword "{keyword}"')

    return result


def favorites_parser(page=None):
    result = []

    if page:
        page_range = page
    else:
        try:
            init = request('get', constant.V2_FAV_URL, params={'page': 1}).json()
        except Exception as e:
            logger.error(f"Can't get favorites: {e}")
            return []

        if 'error' in init:
            logger.error(f"Can't get favorites: {init['error']}")
            return []

        total_pages = init.get('num_pages', 1)
        logger.info(f'Fetching favorites across {total_pages} pages.')

        if os.getenv('DEBUG'):
            page_range = range(1, 2)
        else:
            page_range = range(1, total_pages + 1)

    for p in page_range:
        logger.info(f'Getting doujinshi ids of page {p}')
        i = 0
        while i <= constant.RETRY_TIMES:
            i += 1
            try:
                response = request('get', constant.V2_FAV_URL, params={'page': p}).json()
                if 'result' not in response:
                    logger.warning(f'Failed to get favorites at page {p}, retrying ({i} times) ...')
                    continue
                for row in response['result']:
                    title = (row.get('english_title')
                             or row.get('title', {}).get('english', '')
                             or '')
                    result.append({'id': row['id'], 'title': title})
                break
            except Exception as e:
                logger.warning(f'Error: {e}, retrying ({i} times) ...')

    return result


# ---------------------------------------------------------------------------
# Display helper
# ---------------------------------------------------------------------------

def print_doujinshi(doujinshi_list):
    if not doujinshi_list:
        return
    try:
        term_width = int(os.environ['COLUMNS'])
    except (KeyError, ValueError):
        term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
    # id column ~6 chars + 4 padding/borders; leave the rest for title
    title_width = max(term_width - 10, 40)
    data = [(i['id'], i['title']) for i in doujinshi_list]
    headers = ['id', 'doujinshi']
    logger.info(f'Search Result || Found {len(doujinshi_list)} doujinshis')
    print(tabulate(tabular_data=data, headers=headers, tablefmt='rst',
                   maxcolwidths=[None, title_width]))


if __name__ == '__main__':
    print(doujinshi_parser("32271"))
