import time

from apscheduler.schedulers.blocking import BlockingScheduler

import quartzscrapers as qs


def tick():
    print('Tick tock')


def push_data_to_github():
    print('No operation')


def run_job(scraper):
    start_time = time.time()
    scraper.scrape()

    print('Total scrape took {} s.\n'.format(time.time() - start_time))
    push_data_to_github()


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
    scheduler.add_job(tick, 'interval', seconds=3)

    # Execute every day at 1:00am
    scheduler.add_job(run_job, 'cron', hour=1, args=[qs.News])
    scheduler.add_job(run_job, 'cron', hour=1, args=[qs.Buildings])
    scheduler.add_job(run_job, 'cron', hour=1, args=[qs.Textbooks])
    scheduler.add_job(run_job, 'cron', hour=1, args=[qs.Courses])


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    init_jobs_dev()

    try:
        print('Running jobs')
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
