# coding: utf-8
"""
Adapters that wrap the plugin-specific code to implement the
core plugin interfaces (BaseParser, BaseModel, BaseSerializer).
"""
from typing import Iterator, List, Dict, Tuple

from doujinshi_dl.core.plugin import BaseParser, BaseModel, BaseSerializer, GalleryMeta


class ParserAdapter(BaseParser):
    """Wraps doujinshi_dl_nhentai.parser.doujinshi_parser / search_parser / favorites_parser."""

    def fetch(self, gallery_id: str) -> GalleryMeta:
        from doujinshi_dl_nhentai.parser import doujinshi_parser
        raw = doujinshi_parser(gallery_id)
        if not raw:
            return None  # type: ignore[return-value]
        return _raw_to_meta(raw)

    def artist(self, artist_name: str, sorting: str = 'date', page=None, **kwargs) -> List[Dict]:
        from doujinshi_dl_nhentai.parser import artist_parser
        return artist_parser(artist_name, sorting=sorting, page=page,
                             is_page_all=kwargs.get('is_page_all', False))

    def search(self, keyword: str, sorting: str = 'date', page=None, **kwargs) -> List[Dict]:
        from doujinshi_dl_nhentai.parser import search_parser
        return search_parser(keyword, sorting=sorting, page=page,
                             is_page_all=kwargs.get('is_page_all', False))

    def favorites(self, page=None) -> List[Dict]:
        from doujinshi_dl_nhentai.parser import favorites_parser
        return favorites_parser(page=page)

    def configure(self, args):
        pass


class DoujinshiAdapter(BaseModel):
    """Wraps doujinshi_dl_nhentai.model.Doujinshi, exposes iter_tasks() as (url, filename) pairs."""

    def __init__(self, meta: GalleryMeta, name_format: str = '[%i][%a][%t]'):
        from doujinshi_dl_nhentai.model import Doujinshi
        raw = _meta_to_raw(meta)
        self._doujinshi = Doujinshi(name_format=name_format, **raw)

    @property
    def doujinshi(self):
        return self._doujinshi

    def iter_tasks(self) -> Iterator[Tuple[str, str]]:
        from doujinshi_dl_nhentai.constant import IMAGE_URL
        d = self._doujinshi
        for i in range(1, min(d.pages, len(d.ext)) + 1):
            ext = d.ext[i - 1]
            url = f'{IMAGE_URL}/{d.img_id}/{i}.{ext}'
            filename = f'{i}.{ext}'
            yield url, filename


class SerializerAdapter(BaseSerializer):
    """Wraps doujinshi_dl_nhentai.serializer.serialize_* functions."""

    def write_all(self, meta: GalleryMeta, output_dir: str):
        from doujinshi_dl_nhentai.model import Doujinshi
        from doujinshi_dl_nhentai.serializer import serialize_json, serialize_comic_xml, serialize_info_txt
        raw = _meta_to_raw(meta)
        doujinshi = Doujinshi(**raw)
        serialize_json(doujinshi, output_dir)
        serialize_comic_xml(doujinshi, output_dir)
        serialize_info_txt(doujinshi, output_dir)

    def finalize(self, output_dir: str) -> None:
        from doujinshi_dl_nhentai.serializer import set_js_database
        set_js_database()


# ---------------------------------------------------------------------------
# Helpers: convert between the raw dict format used by parser.py and GalleryMeta
# ---------------------------------------------------------------------------

def _raw_to_meta(raw: dict) -> GalleryMeta:
    """Convert the dict returned by doujinshi_parser() into a GalleryMeta."""
    info_keys = {'subtitle', 'favorite_counts', 'characters', 'artists', 'languages',
                 'tags', 'parodies', 'groups', 'categories', 'date'}
    info = {k: v for k, v in raw.items() if k in info_keys}
    extra = {k: v for k, v in raw.items() if k not in
             {'id', 'name', 'pretty_name', 'img_id', 'ext', 'pages'} | info_keys}
    return GalleryMeta(
        id=str(raw['id']),
        name=raw.get('name', ''),
        pretty_name=raw.get('pretty_name', ''),
        img_id=str(raw.get('img_id', '')),
        ext=raw.get('ext', []),
        pages=int(raw.get('pages', 0)),
        info=info,
        extra=extra,
    )


def _meta_to_raw(meta: GalleryMeta) -> dict:
    """Convert a GalleryMeta back to the flat dict that Doujinshi() accepts."""
    raw = {
        'id': meta.id,
        'name': meta.name,
        'pretty_name': meta.pretty_name,
        'img_id': meta.img_id,
        'ext': meta.ext,
        'pages': meta.pages,
    }
    raw.update(meta.info)
    raw.update(meta.extra)
    return raw
