"""
quartzscrapers.scrapers.buildings.buildings_helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains auxiliary functions for the buildings module.
"""

import googlemaps

from ..utils.config import GOOGLE_MAPS_KEY

GMAPS = None
if GOOGLE_MAPS_KEY:
    GMAPS = googlemaps.Client(key=GOOGLE_MAPS_KEY)

def get_building_coords(address):
    """Use Google Maps API to triangulate geocoordinates of an address.

    Args:
        address: String of an address.

    Returns:
        Tuple of geocoordinates as floats.
    """
    prefix = ', Kingston, ON'
    geocoords = GMAPS.geocode(address + prefix)[0]['geometry']['location']

    return geocoords['lat'], geocoords['lng']
