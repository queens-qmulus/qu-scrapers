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

    Multiple courses with the same ID can exist. Such as MATH121 for main
    campus, bader campus, or online. In order for a course listing to be
    unique, these 6 datapoints must be distinct as a bundle:
    1 - course code
    2 - department
    3 - campus
    4 - academic_level
    5 - year
    6 - term

    Args:
        course_data: Dictionary of course data.
        section_data: Dictionary of course section data.
        scraper: Base scraper object.
        location: String location output files.
    """
    year = course_data['year']
    term = course_data['term']
    campus, *_ = course_data['campus'].split(' ')

    # "Undergraduate Online" => "Undergraduate_Online"
    # "Non-Credit" => "Non_Credit"
    academic_level = '_'.join(
        course_data['academic_level'].replace('-', ' ').split(' ')
    )

    dept = course_data['department']
    code = course_data['course_code']

    key = 'course_sections'
    filepath = '{}/sections'.format(location)
    filename = '{year}_{term}_{academic_level}_{campus}_{dept}_{code}'.format(
        year=year,
        term=term,
        academic_level=academic_level,
        campus=campus,
        dept=dept,
        code=code,
    )

    scraper.update_data(course_data, section_data, key, filename, filepath)
    scraper.logger.debug('Section data saved')
