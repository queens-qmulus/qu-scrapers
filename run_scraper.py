"""TODO

"""
import time

import quartzscrapers as qs

# TODO: get to_scrape list form argv or env
# (so that it can be specified when run in a task)
TO_SCRAPE = [qs.TestScraper.scraper_key]

SCRAPE_SESSION_TIMESTAMP = str(int(time.time()))

if qs.TestScraper.scraper_key in TO_SCRAPE:
    qs.TestScraper.scrape(SCRAPE_SESSION_TIMESTAMP)

if qs.Buildings.scraper_key in TO_SCRAPE:
    qs.Buildings.scrape(SCRAPE_SESSION_TIMESTAMP)

if qs.Textbooks.scraper_key in TO_SCRAPE:
    qs.Textbooks.scrape(SCRAPE_SESSION_TIMESTAMP)

if qs.Courses.scraper_key in TO_SCRAPE:
    qs.Courses.scrape(SCRAPE_SESSION_TIMESTAMP)

if qs.News.scraper_key in TO_SCRAPE:
    qs.News.scrape(SCRAPE_SESSION_TIMESTAMP)
