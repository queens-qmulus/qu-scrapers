"""Script to start a scrape session.

Positional command line arguments:
    argv[1:]: list of modules (indentified by scraper_key) to scrape
"""
import time
import sys

import quartzscrapers as qs

TO_SCRAPE = sys.argv[1:]

START_TIME = int(time.time())
SCRAPE_SESSION_TIMESTAMP = str(START_TIME)

SCRAPERS = [qs.TestScraper, qs.Buildings, qs.Textbooks, qs.Courses, qs.News]

for module in SCRAPERS:
    if module.scraper_key not in TO_SCRAPE:
        continue

    module_start_time = int(time.time())
    print('Starting {} scrape'.format(module.scraper_key))

    module.scrape(SCRAPE_SESSION_TIMESTAMP)

    module_finish_time = int(time.time())
    print('Finished {} scrape in {} seconds'.format(
        module.scraper_key, module_finish_time - module_start_time))

    # TODO: upload metadata and combined dataset to storage
    #   Take code from tasks.py
