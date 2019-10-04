# QU Scrapers: Queen's University Scrapers

// TODO: Qmulus sub-logo

[![Actions Status](https://github.com/queens-qmulus/qu-scrapers/workflows/Python%20application/badge.svg)](https://github.com/queens-qmulus/qu-scrapers/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Gitter](https://img.shields.io/gitter/room/queens-qmulus/community)](https://gitter.im/queens-qmulus/community)

**qu-scrapers** is a library of scrapers for a variety of resources at Queen's University. This is used to compile a series of datasets for [Qmulus](https://github.com/queens-qmulus/qmulus).

## Requirements
- [pipenv](https://github.com/pypa/pipenv)

## Installation

```
git clone https://github.com/queens-qmulus/qu-scrapers.git && cd qu-scrapers

pipenv install
```

## Usage
Add your application configuration to your `.env` file in the root of your project:

```
GITHUB_TOKEN=<YOUR_GITHUB_TOKEN>
GOOGLE_MAPS_KEY=<YOUR_GOOGLE_MAPS_KEY>
GOOGLE_BOOKS_KEY=<YOUR_GOOGLE_BOOKS_KEY>
QUEENS_USERNAME=<YOUR_QUEENS_USERNAME>
QUEENS_PASSWORD=<YOUR_QUEENS_PASSWORD>
```

You may not need all environment variables, depending on what you want to scrape.

Afterwards, you can import the library and choose a scraper to start:

```python
import quartzscrapers as qs

# Scrape https://www.campusbookstore.com for textbooks. Default path is './dumps/textbooks'
qs.Textbooks.scrape()
...

# Scrape http://queensu.ca/maps for textbooks. Default path is ./dumps/buildings'
qs.Buildings.scrape()
```

Alternatively, there's a `run_scraper.py` module to run multiple jobs from the command line:

`pipenv run python textbooks buildings courses ...`

Every scraper has an optional `location` argument to define the data dump filepath. Certain scrapers have additional arguments. For details, see [Library Reference](#library-reference).

## Library Reference

See further documentation for each available scraper:

- [Buildings](quartzscrapers/scrapers/buildings/README.md)
- [Courses](quartzscrapers/scrapers/courses/README.md)
- [News](quartzscrapers/scrapers/news/README.md)
- [Textbooks](quartzscrapers/scrapers/textbooks/README.md)

## Contributing
We welcome contributions! Please feel free to file bugs and questions as well as feature and data set requests in [this repo's issue tracker](https://github.com/queens-qmulus/qu-scrapers/issues).
If you're looking to contribute to QU Scrapers directly, please see the [code contributions guide](CONTRIBUTING.md).

## Contact
If you have any questions or feedback, feel free to contact us at contact@qmulus.io.