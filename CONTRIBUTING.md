# Contributing to QU Scrapers
Please refer to this guide for making direct contributions to the QU Scrapers service.

## How Can I Contribute?
- The easiest way to contribute to QU Scrapers is to file any bugs or feature requests you have in [this repo's issue tracker](https://github.com/queens-qmulus/qu-scrapers/issues)
- Fixing bugs or improving documentation. Take a look [the issue tracker](https://github.com/queens-qmulus/qu-scrapers/issues) for any open bugs or tasks

### Scraper Basics
To get a technical overview of the entire system and to understand how the API service and data scrapers work together, refer to this [system overview diagram](https://docs.google.com/drawings/d/1jeoJlOxrmR5KwAhRTvgbgjOKE1ElvsWg4Mh15_480-o/edit?usp=sharing) and [the original technical design doc](https://docs.google.com/document/d/1mSzL61QNuoLRUKFjVgBNZ3OXuvTTt8ZQlr1hROU5qTE).

We have a base `Scraper` class that handles a lot of the functionality of every scraper, such as reading/writing to memory, error handling, and HTTP requests. Every new scraper uses this class for common functionality, along with a `scrape` method for custom scraping.

Every scraper has the same top-level variables that have custom information:

- `scraper_key`: The scraper slug name used by the `run_scraper` script to uniquely identify scrapers
- `location`: Default path to store the scraper's JSON data
- `host`: The URL the scraper will be  requesting from
- `scraper`: The instantiated base scraper from `scraper.py`
- `logger`: The base scraper's logger

You can look at any of the existing scrapers as an example of how these are used and declared.

### Adding a new scraper

Scraping can be more of an art than just purely a science. The general rule of thumb is:

1. Decide and agree upon a Queen's public website to scrape. Find the right URL (e.g.: [http://www.queensu.ca/maps](http://www.queensu.ca/maps) is used for `buildings.py`, [https://www.campusbookstore.com](https://www.campusbookstore.com) for `textbooks.py`, etc), and explore the step-by-step process your scraper would use to access the desired information.
2. Create your scraper class and use the base scraper `scraper.py`.
3. Declare the top-level scraper attribute variables to be used for a particular scrape, including the URL as the `host`.
4. Create your `scrape` method, with a series of steps for parsing the desired information.

**Note: Please remember to use `scraper.wait()` after a network request so we don't hit Queen's servers aggressively. The more respectful we try to be with our scraping, the better it is for Queen's admin and students who use these services.**

You can look at any of the existing scrapers as an example of how the development process is done.


## Making Your First Contribution
First, fork and clone this repo.

### Running QU Scrapers Locally
Following the [installation](README.md#installation) and [usage](README.md#usage) guides are the quickest ways to set up and run this application.

#### Environment configuration
QU Scrapers uses environment variables for configuration. To use custom env variables while running locally, create a `.env` file in the root of the repo (this will/should not get commited to the repo).

### Make Your Changes
- If your change requires a new scraper module:
  - Ensure one successful scrape session, even if manually tested. We will not accept new scrapers until we can verify that the scraper runs reliably and produces valid data
  - Open a PR to discuss what new scraper you want to add and what the data schema will look like.

### Open a Pull Request
When your changes are ready, open a PR against the `develop` branch. Some things to keep in mind:
- Make sure your branch is up to date (rebase your branch against `develop` or merge `develop` into your branch). This way our checks will run against the latest changes.
- Github will run several checks against your branch:
  - [Flake8 Style Guide](http://flake8.pycqa.org/) linting
  - The existing test suite and any new tests you add
- Add any Github issue numbers that were resolved in the PR description.
- Write a small blurb with some stats on a succesful scrape, such as total time, the machine you ran it on, the number of records your scrape collected, etc. This is valuable information for how involved these scrapers will be.
- Add a small README.md within the directory of your scrape that includes information such as the data schema, the JSON filename format, and any subtle nuances with how your scrape works or what you've seen during scrapes (remember; scraping can be a mix of an art and a science, so this is helpful for others to see). Check out [Textbooks](quartzscrapers/scrapers/textbooks/README.md) or [Courses](quartzscrapers/scrapers/courses/README.md) for an example. These can be as straightforward or as detailed as you think they need to be.
- Add one of the project maintainers to your PR, we'll aim to review your PR within one day.

Currently, there is no schedule for production deployments but your changes will likely be deployed within the week.

Scrapers and datasets are also run and uploaded manually for the time being. If you have a new scraper or scraper changes you want in effect,
contact the maintainers and they will manually run these jobs.
