import yaml
import logging.config

from quartzscrapers.scrapers.buildings import Buildings

from quartzscrapers.scrapers.news import (
    News,
    Journal,
    Gazette,
    AlumniReview,
    SmithMagazine,
    JurisDiction,
    )

from quartzscrapers.scrapers.textbooks import Textbooks

from quartzscrapers.scrapers.courses import Courses

filepath = './quartzscrapers'

with open('{}/logging.yaml'.format(filepath), 'r') as file:
    config = file.read().format(
        format='simple', filepath='{}/logs'.format(filepath), prefix=''
    )

logging.config.dictConfig(yaml.safe_load(config))
