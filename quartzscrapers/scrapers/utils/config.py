"""
quartzscrapers.scrapers.utils.config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains environment variables retrieved from local .env file
"""

import os

GOOGLE_MAPS_KEY = os.environ.get('GOOGLE_MAPS_KEY')
GOOGLE_BOOKS_KEY = os.environ.get('GOOGLE_BOOKS_KEY')
QUEENS_USERNAME = os.environ.get('QUEENS_USERNAME')
QUEENS_PASSWORD = os.environ.get('QUEENS_PASSWORD')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
