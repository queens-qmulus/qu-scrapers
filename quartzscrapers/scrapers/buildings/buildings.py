from urllib.parse import urljoin

from ..utils import Scraper
from .helpers import get_building_coords


class Buildings:
    '''
    A scraper for Queen's buildings.

    Queen's campus map is currently located at http://queensu.ca/maps
    '''

    host = 'http://www.queensu.ca'

    @staticmethod
    def scrape():
        '''Update database records for buildings scraper'''

        campuses = Buildings.get_campuses('campusmap/overall')

        for campus in campuses:
            campus_relative_url = campus.find('a')['href']
            buildings = Buildings.get_buildings(campus_relative_url)

            for building in buildings:
                results = []

                try:
                    building_data = Buildings.parse_data(
                        campus_relative_url,
                        building['href']
                        )

                    if building_data:
                        results.append(building_data)
                        Scraper.save_data(results, 'buildings')

                except Exception as ex:
                    Scraper.handle_error(ex, 'scrape')

                Scraper.wait()


    @staticmethod
    def get_campuses(relative_url):
        '''
        Get list of campus URLs as BeautifulSoup HTML tags

        Returns:
            List[bs4.element.Tag]
        '''

        campus_overall_url = urljoin(Buildings.host, relative_url)
        soup = Scraper.get_url(campus_overall_url)
        campuses = soup.find_all('p', 'overall-label')

        return campuses


    @staticmethod
    def get_buildings(campus_relative_url):
        '''
        Get list of relative building URLs as BeautifulSoup HTML tags

        Returns:
            List[bs4.element.Tag]
        '''

        # pull campus name from relative url, such as /campusmap/west,
        # which splits by '/' and grab the last value
        campus_name = campus_relative_url.split('/')[-1]

        print('Campus: {campus}'.format(campus=campus_name.upper()))
        print('========================\n')

        campus_url = urljoin(Buildings.host, campus_relative_url)
        soup = Scraper.get_url(campus_url)
        campus_map = soup.find('map')
        buildings = campus_map.find_all('area')

        return buildings


    @staticmethod
    def parse_data(campus_relative_url, building_param):
        '''
        Parse data from building tags

        Returns:
            Object
        '''

        print('Building Parameter: {param}'.format(param=building_param))

        building_relative_url = urljoin(campus_relative_url, building_param)
        building_url = urljoin(Buildings.host, building_relative_url)
        soup = Scraper.get_url(building_url)

        campus_map = soup.find('map')
        building = campus_map.find('area', href=building_param)
        building_fields = soup.find_all('div', 'building-field')

        # Omit 'Building Code:' from section
        code = building_fields[1].text.strip()[14:]
        name = soup.find('div', 'title').text.strip()
        address = building_fields[0].find('a').text.strip()
        polygon_raw = building['coords'].split(', ')

        # convert polygon coords into tuple of integer pairs
        polygon = [(int(p[0]), int(p[1])) for p in polygon_raw]

        campus_name = campus_relative_url.split('/')[-1]
        latitude, longitude = get_building_coords(address)

        data = {
            'code': code,
            'name': name,
            'address': address,
            'latitude': latitude,
            'longitude': longitude,
            'campus': campus_name,
            'polygon': polygon,
        }

        return data
