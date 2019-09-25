"""Integration tests for qmulus scrapers."""

import unittest
import os
import json
import quartzscrapers.scrapers.test_scraper as ts

class TestScraper(unittest.TestCase):
    """A simple scraper test that provides minimal coverage of
    core scraper components. This test scrapes the TestScraper module
    and verifies that the metadata file is written correctly.
    """

    def test_scraper(self):
        """Verifies that the test scraper outputs valid json data."""
        dir_path = './dumps/test_scraper'
        ts.TestScraper.scrape(dir_path)

        basename = os.listdir(dir_path)[0]
        first_file = dir_path + '/' + basename

        if os.path.isfile(first_file):
            with open(first_file, 'r+') as file:
                try:
                    parsed_json = json.loads(file.read())
                    self.assertIsNotNone(parsed_json[0]['title'])
                    self.assertIsNotNone(parsed_json[0]['link'])
                except Exception:
                    self.fail('Couldn\'t parse JSON dataset')
        else:
            self.fail('No JSON file written')


if __name__ == '__main__':
    unittest.main()
