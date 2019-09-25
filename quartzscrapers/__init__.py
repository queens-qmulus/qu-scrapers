"""
Quartz Scrapers
~~~~~~~~~~~~~~~

Quartz-scrapers is a compilation of scraper modules that aggregate everything
related to Queen's University. Basic usage is as simple as:

  >>> import quartzscrapers as qs
  >>> qs.Courses.scrape()

Full documentation is as <http://placeholder.io>.
"""


import logging.config

import yaml

from quartzscrapers.scrapers.test_scraper import TestScraper
from quartzscrapers.scrapers.buildings import Buildings
from quartzscrapers.scrapers.textbooks import Textbooks
from quartzscrapers.scrapers.courses import Courses
from quartzscrapers.scrapers.news import (
    News,
    Journal,
    Gazette,
    AlumniReview,
    SmithMagazine,
    JurisDiction,
)

FILEPATH = './quartzscrapers'

with open('{}/logging.yaml'.format(FILEPATH), 'r') as file:
    CONFIG = file.read().format(
        format='simple', filepath='{}/logs'.format(FILEPATH), prefix=''
    )

logging.config.dictConfig(yaml.safe_load(CONFIG))
