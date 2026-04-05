import unittest
import os
import urllib3.exceptions

from doujinshi_dl_nhentai import constant
from doujinshi_dl_nhentai.parser import galleries_by_tag_parser, search_parser, doujinshi_parser, favorites_parser


class TestParser(unittest.TestCase):
    def setUp(self) -> None:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        constant.CONFIG['cookie'] = os.getenv('DDL_COOKIE')
        constant.CONFIG['useragent'] = os.getenv('DDL_UA')

    def test_galleries_by_tag(self):
        result = galleries_by_tag_parser(2937, 'recent', [1], False, 5) # big breasts
        self.assertTrue(len(result) is 5)

    def test_search(self):
        result = search_parser('umaru', 'recent', [1], False)
        self.assertTrue(len(result) > 0)

    def test_doujinshi_parser(self):
        result = doujinshi_parser(123456)
        self.assertTrue(result['pages'] == 84)

    def test_favorites_parser(self):
        result = favorites_parser(page=[1])
        self.assertTrue(len(result) > 0)
