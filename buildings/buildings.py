import time
import googlemaps

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import add_default_fields, save_data, requests_retry_session

GOOGLE_MAPS_KEY = 'AIzaSyAysepZt8npudoPnYbeQjR0GzR4sUA_PmU'

base_url = 'http://www.queensu.ca'
gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)

def scrape():
    url = urljoin(base_url, 'campusmap/overall')

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        campuses = soup.find_all('p', 'overall-label')

        for campus in campuses:
            campus_link = campus.find('a')['href']

            # pull campus name from relative link, such as
            # /campusmap/west, which  splits by '/'' and grab the last value
            campus_name = campus_link.split('/')[-1]

            print('Campus: {campus}'.format(campus=campus_name.upper()))
            print('========================\n')

            crawl_campus(campus_link, campus_name)

    except Exception as ex:
        print('Error in scrape(): {ex}'.format(ex=ex))


def crawl_campus(url, campus):
    url = urljoin(base_url, url)

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        campus_map = soup.find('map')
        buildings = campus_map.find_all('area')

        for building in buildings:
            try:
                results = []
                building_data = scrape_building(url, building['href'])

                if building_data:
                    results.append(add_default_fields(building_data, campus))
                    save_data(results, 'buildings')

            except Exception as ex:
                print('Error in crawl_campus(): {ex}'.format(ex=ex))

            print('Waiting 2 seconds...')
            time.sleep(2)

    except Exception as ex:
        print('Error in crawl_campus(): {ex}'.format(ex=ex))


def scrape_building(url, param):
    url = urljoin(url, param)

    print('Building Parameter: {param}'.format(param=param))

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        campus_map = soup.find('map')

        building = campus_map.find('area', href=param)
        building_fields = soup.find_all('div', 'building-field')

        # Omit 'Building Code:' from section
        code = building_fields[1].text.strip()[14:]
        name = soup.find('div', 'title').text.strip()
        address = building_fields[0].find('a').text.strip()
        polygon = building['coords'].split(', ')

        geocoords = gmaps.geocode(address + ', Kingston, ON')[0]['geometry']['location']

        latitude = geocoords['lat']
        longitude = geocoords['lng']

        data = {
            'code': code,
            'name': name,
            'address': address,
            'latitude': latitude,
            'longitude': longitude,
            # convert polygon coords into array of integer pairs
            'polygon': [[int(p[0]), int(p[1])] for p in polygon],
        }

        return data

    except Exception as ex:
        print('Error in scrape_building(): {ex}'.format(ex=ex))


if __name__ == '__main__':
    start_time = time.time()
    scrape()
    total_time = time.time() - start_time

    print('Total scrape took {seconds} s.\n'.format(seconds=total_time))
