import googlemaps

from ..utils.config import GOOGLE_MAPS_KEY

gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)


def get_building_coords(address):
    prefix = ', Kingston, ON'
    geocoords = gmaps.geocode(address + prefix)[0]['geometry']['location']

    return geocoords['lat'], geocoords['lng']
