"""
run_scraper
~~~~~~~~~~~

Script to start a scrape session.

Positional command line arguments:
    argv[1:]: list of modules (indentified by scraper_key) to scrape
"""
import os
import time
import sys

import github

import quartzscrapers as qs
from quartzscrapers.scrapers.utils.config import GITHUB_TOKEN

TO_SCRAPE = sys.argv[1:]
ORG = 'queens-qmulus'
REPO = 'datasets-scraps'
SCRAPERS = [
    qs.TestScraper,
    qs.Buildings,
    qs.Textbooks,
    qs.Courses,
    qs.News,
]


def push_to_github(scraper_name):
    """Aggregate files into one compiled file and automate a push to GitHub.

    Args:
        scraper_name: Name of the passed scraper class.
    """
    repo = github.Github(GITHUB_TOKEN).get_organization(ORG).get_repo(REPO)
    files = merge_files(scraper_name)

    for filename in files:
        output = '/{}'.format(filename.split('/')[-1])
        message = 'Export dataset: {}'.format(filename.split('/')[-1][:-5])

        with open(filename, 'r') as file:
            try:
                file_repo = repo.get_contents(output)
                file_disk = file.read()

                # Only commit if there are changes to push.
                if file_repo.decoded_content.decode("utf-8") != file_disk:
                    print('Updating existing file')
                    repo.update_file(
                        output.strip('/'),
                        message,
                        file_disk,
                        file_repo.sha,
                    )

            # File doesn't exist, meaning it's a new file to commit.
            except github.UnknownObjectException:
                print('New file detected. Creating for commit...')
                repo.create_file(output.strip('/'), message, file.read())


def merge_files(filename, filepath='./dumps'):
    """Compile multiple files from an executed scrape into one compiled file.

    Access the resulting directory of a scraper's JSON files and consolidate
    into one compiled JSON file. Sub-directories will be shallowly accessed
    to create compiled files of the sub-directory.

    E.g: For courses, courses/sections, courses/departments, courses/courses
    result in sections.json, departments.json and courses.json.

    Args:
        filename: String of the directory in question.
        filepath (optional): Location of the directory in question.

    Returns:
        A list of the locations of the resulting compiled files.
    """
    filepaths = []
    file_dir = './data'
    filepath = '{}/{}'.format(filepath, filename)

    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    # Check if the filepath has any subdirectories or files.
    _, directories, files = next(os.walk(filepath))

    if directories:
        for directory in directories:
            path_in = '{}/{}'.format(filepath, directory)
            path_out = '{}/{}.json'.format(file_dir, directory)
            filepaths.append(path_out)

            _, _, files = next(os.walk(path_in))
            write_files(path_in, path_out, files)
    else:
        path_out = '{}/{}.json'.format(file_dir, filename)

        filepaths.append(path_out)
        write_files(filepath, path_out, files)

    return filepaths


def write_files(path_in, path_out, files):
    """Compiles multiple files into one file.

    Args:
        path_in: Input location of directory of files.
        path_out: Output location to write the compiled file.
        files: List of filenames to repeat this process for.
    """
    with open(path_out, 'w') as merged_file:
        for filename in files:
            with open('{}/{}'.format(path_in, filename), 'r') as file:
                # Flatten nested, raw JSON files
                merged_file.write(
                    file.read().replace('\n', '').replace('  ', '') + '\n')


for module in SCRAPERS:
    if module.scraper_key not in TO_SCRAPE:
        continue

    module_start_time = int(time.time())
    print('Starting {} scrape'.format(module.scraper_key))

    module.scrape()

    module_finish_time = int(time.time())
    print('Finished {} scrape in {} seconds'.format(
        module.scraper_key, module_finish_time - module_start_time))

    # Upload combined dataset to storage.
    push_to_github(module.scraper_key)
