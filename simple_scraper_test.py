"""TODO"""

import unittest

import os
import json
import quartzscrapers.scrapers.test_scraper as ts


class TestSimpleScraperE2E(unittest.TestCase):
    """TODO"""

    def test_scraper(self):
        """TODO"""
        scrape_session_timestamp = 'test_scrape_unix_timestamp'
        ts.TestScraper.scrape(scrape_session_timestamp)

        metadata_filepath = ('./dumps/' +
                             scrape_session_timestamp + '/metadata.json')
        if os.path.isfile(metadata_filepath):
            with open(metadata_filepath, 'r+') as file:
                try:
                    content_dict = json.loads(file.read())
                    self.assertEqual(
                        content_dict['scrape_session_timestamp'],
                        scrape_session_timestamp)
                    self.assertEqual(
                        content_dict[ts.TestScraper.scraper_key]["status"],
                        "SUCCESS")
                except Exception:
                    self.fail('Incorrect metadata file written')
        else:
            self.fail('No metadata file written')

        # TODO: more thoroughly verify that this succeeded


if __name__ == '__main__':
    unittest.main()
