import unittest

from crawler.domain_crawler import DomainCrawler


class DomainDiscoveryTests(unittest.TestCase):
    def test_akamai_block_has_actionable_error(self):
        crawler = DomainCrawler()

        message = crawler._blocked_message(
            403,
            "<title>Access Denied</title> errors.edgesuite.net",
        )

        self.assertIn("Akamai", message)
        self.assertIn("HTTP 403", message)
        self.assertIn("local crawl", message)


if __name__ == "__main__":
    unittest.main()
