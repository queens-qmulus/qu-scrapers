import os
import time

import github

from apscheduler.schedulers.blocking import BlockingScheduler

import quartzscrapers as qs

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']


def run_job(scraper):
    start_time = time.time()
    scraper.scrape()

    print('Total scrape took {} s.\n'.format(time.time() - start_time))
    push_to_github(scraper.__name__)


def init_jobs():
    # Execute every Sunday at 2:00am
    scheduler.add_job(
        run_job, 'cron', day_of_week='sun', hour=2, args=[qs.News])

    # Execute the first Sunday of every month at 2:00am
    scheduler.add_job(
        run_job, 'cron', day='sun', hour=2, args=[qs.Buildings])

    # Execute the first Sunday every August and December at 2:00am
    scheduler.add_job(
        run_job, 'cron', month='8,12', day='sun', hour=2, args=[qs.Textbooks])

    # Note: According to Queen's ITS, standard maintenance periods are
    # Tuesdays to Thursdays from 5am to 7:30am and Sundays from 5am to 10am
    # Source: http://www.queensu.ca/its/apps/notices/myqueensu_outage.php

    # Execute the first Monday every August and December at 1:00am
    scheduler.add_job(
        run_job, 'cron', month='8,12', day='mon', hour=1, args=[qs.Courses])


def init_jobs_dev():
    # Execute every day at 1:00am
    scheduler.add_job(run_job, 'cron', hour=1, args=[qs.News])
    scheduler.add_job(run_job, 'cron', hour=1, args=[qs.Buildings])
    scheduler.add_job(run_job, 'cron', hour=1, args=[qs.Textbooks])
    scheduler.add_job(run_job, 'cron', hour=1, args=[qs.Courses])


def push_to_github(scraper_name='Buildings'):
    repo = github.Github(GITHUB_TOKEN).get_user().get_repo('qmulus-test')
    files = merge_files(scraper_name)

    for file in files:
        output = '/{}'.format(file.split('/')[-1])
        message = 'Export dataset: {}'.format(file.split('/')[-1][:-5])

        with open(file, 'r') as f:
            try:
                file_repo = repo.get_file_contents(output)
                file_disk = f.read()

                # Only commit if there are changes to push
                if file_repo.decoded_content.decode("utf-8") != file_disk:
                    print('Updating existing file')
                    repo.update_file(output, message, file_disk, file_repo.sha)

            # file doesn't exist, meaning it's a new file to commit
            except github.UnknownObjectException as ex:
                print('New file detected. Creating for commit...')
                repo.create_file(output, message, f.read())


def merge_files(filename, filepath='./dumps'):
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
    with open(path_out, 'w') as merged_file:
        for file in files:
            with open('{}/{}'.format(path_in, file), 'r') as f:

                # Flatten the raw JSON files, which are nested
                merged_file.write(
                    f.read().replace('\n', '').replace('  ', '') + '\n')


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    init_jobs_dev()

    try:
        print('Running jobs')
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
