import os
import unittest
import urllib3.exceptions

from doujinshi_dl_nhentai import constant
from doujinshi_dl_nhentai.http import check_cookie


class TestLogin(unittest.TestCase):
    def setUp(self) -> None:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        constant.CONFIG['cookie'] = os.getenv('DDL_COOKIE')
        constant.CONFIG['useragent'] = os.getenv('DDL_UA')

    def test_cookie(self):
        try:
            check_cookie()
            self.assertTrue(True)
        except Exception as e:
            self.assertIsNone(e)


if __name__ == '__main__':
    unittest.main()
