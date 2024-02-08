from collections.abc import Callable
import unittest
from discord_native_reddit_vids.download import DownloadHandler
import re


class DownloadTest(unittest.TestCase):
    reddit_downloader: DownloadHandler

    def setUp(self):
        self.reddit_downloader = DownloadHandler(
            verbose_name="Reddit Downloader",
            name="reddit",
            url_regexes=[
                re.compile(
                    r"(https?\:\/\/((old\.|www\.)?reddit\.com\/r\/[\w]+\/[\w]*\/[\w]+\/\S*))",
                ),
                re.compile(r"https?\:\/\/v\.redd\.it\/[\w]+"),
                re.compile(r"https?\:\/\/www\.reddit\.com\/r\/[\w]+/s/[\w]+"),
            ],
        )

    def test_url_subreddit(self):
        message_str = """ Hi this is a test message with a some urls!
            https://www.reddit.com/r/aww/comments/7x5z5l/this_is_my_dog_copper_he_has_a_very_unique_bark/
            And here a short url: https://v.redd.it/7x5z5l
            
            also here is a shared link: https://www.reddit.com/r/wizardposting/s/GQ4hi1FDel"""

        ulrs = self.reddit_downloader.extract_urls(message_str)

        self.assertCountEqual(
            ulrs,
            [
                "https://www.reddit.com/r/aww/comments/7x5z5l/this_is_my_dog_copper_he_has_a_very_unique_bark/",
                "https://www.reddit.com/r/wizardposting/s/GQ4hi1FDel",
                "https://v.redd.it/7x5z5l",
            ],
        )

    def test_download(self):
        file1_path = self.reddit_downloader.download("https://v.redd.it/u5ln36ma3fgc1")
        file2_path = self.reddit_downloader.download(
            "https://www.reddit.com/r/wizardposting/s/90ScIvhOqw"
        )

        self.assertTrue(file1_path.exists())
        self.assertTrue(file2_path.exists())
