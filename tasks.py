"""
tasks
~~~~~

This modules handles the scheduled tasks of each scraper, along with automating
the exports of their data to GitHub.
"""

import os
import time

import github
from apscheduler.schedulers.blocking import BlockingScheduler

import quartzscrapers as qs
from quartzscrapers.scrapers.utils.config import GITHUB_TOKEN


def run_job(scraper):
    """Execute a given scraper and push contents to Github server.

    Args:
        scraper: A scraper object.
    """
    start_time = time.time()
    scraper.scrape()

    print('Total scrape took {} s.\n'.format(time.time() - start_time))
    push_to_github(scraper.__name__)


def init_jobs():
    """Initialize scraper jobs."""
    # Execute every Sunday at 2:00am
    SCHEDULER.add_job(
        run_job, 'cron', day_of_week='sun', hour=2, args=[qs.News])

    # Execute the first Sunday of every month at 2:00am
    SCHEDULER.add_job(
        run_job, 'cron', day='sun', hour=2, args=[qs.Buildings])

    # Execute the first Sunday every August and December at 2:00am
    SCHEDULER.add_job(
        run_job, 'cron', month='8,12', day='sun', hour=2, args=[qs.Textbooks])

    # Note: According to Queen's ITS, standard maintenance periods are
    # Tuesdays to Thursdays from 5am to 7:30am and Sundays from 5am to 10am
    # Source: http://www.queensu.ca/its/apps/notices/myqueensu_outage.php

    # Execute the first Monday every August and December at 1:00am
    SCHEDULER.add_job(
        run_job, 'cron', month='8,12', day='mon', hour=1, args=[qs.Courses])


def init_jobs_dev():
    """Initialize scraper jobs (for testing only)."""
    # Execute every day at 1:00am
    SCHEDULER.add_job(run_job, 'cron', hour=1, args=[qs.News])
    SCHEDULER.add_job(run_job, 'cron', hour=1, args=[qs.Buildings])
    SCHEDULER.add_job(run_job, 'cron', hour=1, args=[qs.Textbooks])
    SCHEDULER.add_job(run_job, 'cron', hour=1, args=[qs.Courses])


def push_to_github(scraper_name):
    """Aggregate files into one compiled file and automate a push to GitHub.

    Args:
        scraper_name: Name of the passed scraper class.
    """
    repo = github.Github(GITHUB_TOKEN).get_user().get_repo('qmulus-test')
    files = merge_files(scraper_name)

    for filename in files:
        output = '/{}'.format(filename.split('/')[-1])
        message = 'Export dataset: {}'.format(filename.split('/')[-1][:-5])

        with open(filename, 'r') as file:
            try:
                file_repo = repo.get_file_contents(output)
                file_disk = file.read()

                # Only commit if there are changes to push
                if file_repo.decoded_content.decode("utf-8") != file_disk:
                    print('Updating existing file')
                    repo.update_file(output, message, file_disk, file_repo.sha)

            # file doesn't exist, meaning it's a new file to commit
            except github.UnknownObjectException:
                print('New file detected. Creating for commit...')
                repo.create_file(output, message, file.read())


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
    filepath = '{}/{}'.format(filepath, filename.lower())

    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    # checks if the filepath has any subdirectories or files.
    _, directories, files = next(os.walk(filepath))

    if directories:
        for directory in directories:
            path_in = '{}/{}'.format(filepath, directory)
            path_out = '{}/{}.json'.format(file_dir, directory)
            filepaths.append(path_out)

            _, _, files = next(os.walk(path_in))
            write_files(path_in, path_out, files)
    else:
        path_out = '{}/{}.json'.format(file_dir, filename.lower())

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


if __name__ == '__main__':
    SCHEDULER = BlockingScheduler()
    init_jobs_dev()

    try:
        print('Running jobs')
        SCHEDULER.start()
    except (KeyboardInterrupt, SystemExit):
        pass
