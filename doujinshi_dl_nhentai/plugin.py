# coding: utf-8
from doujinshi_dl.core.plugin import BasePlugin, GalleryMeta
from doujinshi_dl_nhentai.adapters import (
    ParserAdapter,
    DoujinshiAdapter,
    SerializerAdapter,
)


class Plugin(BasePlugin):
    name = "nhentai"

    def create_parser(self) -> ParserAdapter:
        return ParserAdapter()

    def create_model(self, meta: GalleryMeta, name_format: str = '[%i][%a][%t]') -> DoujinshiAdapter:
        return DoujinshiAdapter(meta, name_format=name_format)

    def create_serializer(self) -> SerializerAdapter:
        return SerializerAdapter()

    def check_auth(self) -> None:
        from doujinshi_dl_nhentai.http import check_cookie
        check_cookie()

    def print_results(self, results) -> None:
        from doujinshi_dl_nhentai.parser import print_doujinshi
        print_doujinshi(results)

    def configure(self, args) -> None:
        from doujinshi_dl_nhentai import constant as C
        from doujinshi_dl.core import config as core_config
        if getattr(args, 'cookie', None):
            C.CONFIG['cookie'] = args.cookie
        if getattr(args, 'proxy', None):
            C.CONFIG['proxy'] = args.proxy
        if getattr(args, 'useragent', None):
            C.CONFIG['useragent'] = args.useragent
        if getattr(args, 'language', None):
            C.CONFIG['language'] = args.language
        if getattr(args, 'template', None):
            C.CONFIG['template'] = args.template
        if getattr(args, 'retry', None):
            C.RETRY_TIMES = int(args.retry)
        core_config.set('history_path', C.PLUGIN_HISTORY)
        # Expose commonly-needed values so command.py stays plugin-agnostic
        core_config.set('base_url', C.BASE_URL)
        core_config.set('plugin_config', C.CONFIG)


# Legacy alias
NhentaiPlugin = Plugin
