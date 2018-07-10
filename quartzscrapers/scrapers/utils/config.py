"""
quartzscrapers.scrapers.utils.config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains environment variables retrieved from local .env file
"""

import os

GOOGLE_MAPS_KEY = os.environ['GOOGLE_MAPS_KEY']
GOOGLE_BOOKS_KEY = os.environ['GOOGLE_BOOKS_KEY']
QUEENS_USERNAME = os.environ['QUEENS_USERNAME']
QUEENS_PASSWORD = os.environ['QUEENS_PASSWORD']
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
