from ..utils import Scraper


def save_department_data(department_data, location):
    filename = department_data['code']
    filepath = '{}/departments'.format(location)

    Scraper.write_data(department_data, filename, filepath)
    print('Department data saved\n')

def save_course_data(course_data, location):
    dept, code = course_data['department'], course_data['course_code']
    filename = '{dept}_{code}'.format(dept=dept, code=code)
    filepath = '{}/courses'.format(location)

    Scraper.write_data(course_data, filename, filepath)
    print('Course data saved\n')

def save_section_data(course_data, section_data, location):
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
    """
    year = course_data['year']
    term = course_data['term']
    campus, *_ = course_data['campus'].split(' ')

    # "Undergraduate Online" => "Undergraduate_Online"
    academic_level = '_'.join(course_data['academic_level'].split(' '))
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

    Scraper.update_data(course_data, section_data, key, filename, filepath)

    print('Section data saved\n')
