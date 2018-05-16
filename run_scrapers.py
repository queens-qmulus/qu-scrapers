import time

import quartzscrapers as qs

if __name__ == '__main__':
    start_time = time.time()
    qs.Textbooks.scrape()
    total_time = time.time() - start_time

    print('Total scrape took {seconds} s.\n'.format(seconds=total_time))
