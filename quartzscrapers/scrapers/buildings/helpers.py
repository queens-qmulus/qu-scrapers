import googlemaps
# from .buildings import Buildings

GOOGLE_MAPS_KEY = 'AIzaSyAysepZt8npudoPnYbeQjR0GzR4sUA_PmU'
gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)

def add_default_fields(data, campus):
    data['campus'] = campus

    return data

def get_building_coords(address):
    prefix = ', Kingston, ON'
    geocoords = gmaps.geocode(address + prefix)[0]['geometry']['location']

    return geocoords['lat'], geocoords['lng']