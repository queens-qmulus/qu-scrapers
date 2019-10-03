"""Script to start a scrape session.

Positional command line arguments:
    argv[1:]: list of modules (indentified by scraper_key) to scrape
"""
import time
import sys

import quartzscrapers as qs

TO_SCRAPE = sys.argv[1:]
SCRAPERS = [
    qs.TestScraper,
    qs.Buildings,
    qs.Textbooks,
    qs.Courses,
    qs.News,
]

for module in SCRAPERS:
    if module.scraper_key in TO_SCRAPE:
        module_start_time = int(time.time())
        print('Starting {} scrape'.format(module.scraper_key))

        module.scrape()

        module_finish_time = int(time.time())
        print('Finished {} scrape in {} seconds'.format(
            module.scraper_key, module_finish_time - module_start_time))

        # TODO: upload metadata and combined dataset to storage
        #   Take code from tasks.py
