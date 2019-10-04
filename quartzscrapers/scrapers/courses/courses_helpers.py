"""
quartzscrapers.scrapers.courses.courses_helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains auxiliary functions for the courses module.
"""

import logging.config

import yaml
import pendulum


def setup_logging():
    """Initialize logging."""
    filepath = './quartzscrapers'

    with open('{}/logging.yaml'.format(filepath), 'r') as file:
        config = file.read().format(
            format='verbose',
            filepath='{}/logs'.format(filepath),
            prefix='courses_'
        )

    logging.config.dictConfig(yaml.safe_load(config))

    return logging.getLogger(__name__)


def parse_datetime(datetime):
    """Parse datetimes in ISO format"""
    return pendulum.parse(datetime, strict=False).isoformat().split('T')


def make_course_id(year, term, a_lvl, campus, dept, code, delim, is_file=True):
    """Creates unique identifier out of course data.

    Multiple courses with the same ID can exist. Such as MATH121 for main
    campus, bader campus, or online. In order for a course listing to be
    unique, these 6 datapoints must be distinct as a bundle:
    1 - course code
    2 - department
    3 - campus
    4 - academic_level
    5 - year
    6 - term

    E.g: A formatted ID would be '2018_Summer_Graduate_Main_SOCY_895' if it
    were a file, and '2018-Summer-Graduate-Main-SOCY-895' otherwise.

    Args:
        year: Course year.
        term: Course term.
        a_lvl: Course academic level
        campus: Course campus.
        dept: Course department.
        code: Course code.
        delim: String for type of delimiter separate pieces of info.
        is_file (optional): Bool that determines format of academic level.
    """
    campus, *_ = campus.split(' ')

    # E.g. 1: "Non-Credit" => "Non_Credit" if for files.
    # E.g. 2: "Undergraduate Online" => "Undergraduate-Online" for regular IDs.
    a_lvl = delim.join(a_lvl.replace('-', ' ').split(' '))

    if not is_file:
        term = term.upper()[:2]
        campus = campus[0]
        a_lvl = ''.join([word[0] for word in a_lvl.split(delim)])

    return '{year}{d}{term}{d}{a_lvl}{d}{campus}{d}{dept}{d}{code}'.format(
        d=delim,
        year=year,
        term=term,
        a_lvl=a_lvl,
        campus=campus,
        dept=dept,
        code=code,
    )


def save_department_data(department_data, scraper, location):
    """Write department data to JSON file.

    Args:
        department_data: Dictionary of department data.
        scraper: Base scraper object.
        location: String location output files.
    """
    filename = department_data['code']
    filepath = '{}/departments'.format(location)

    scraper.write_data(department_data, filename, filepath)
    scraper.logger.debug('Department data saved')


def save_course_data(course_data, scraper, location):
    """Write course data to JSON file.

    Args:
        course_data: Dictionary of course data.
        scraper: Base scraper object.
        location: String location output files.
    """
    dept, code = course_data['department'], course_data['course_code']
    filename = '{dept}_{code}'.format(dept=dept, code=code)
    filepath = '{}/courses'.format(location)

    scraper.write_data(course_data, filename, filepath)
    scraper.logger.debug('Course data saved')


def save_section_data(course_data, section_data, scraper, location):
    """Preprocess and save course section data to JSON.

    Args:
        course_data: Dictionary of course data.
        section_data: Dictionary of course section data.
        scraper: Base scraper object.
        location: String location output files.
    """

    key = 'course_sections'
    filepath = '{}/sections'.format(location)
    filename = make_course_id(
        course_data['year'],
        course_data['term'],
        course_data['academic_level'],
        course_data['campus'],
        course_data['department'],
        course_data['course_code'],
        '_',
    )

    scraper.update_data(course_data, section_data, key, filename, filepath)
    scraper.logger.debug('Section data saved')
