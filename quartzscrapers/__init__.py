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

# with open(os.path.join(os.path.dirname(__file__), 'logging.yaml'), 'r') as file:
with open('{}/logging.yaml'.format(filepath), 'r') as file:
    config = file.read().format(filepath=filepath)

logging.config.dictConfig(yaml.safe_load(config))
