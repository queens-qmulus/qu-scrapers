import re

from urllib.parse import urljoin

from ..utils import Scraper
from .buildings_helpers import get_building_coords


class Buildings:
    '''
    A scraper for Queen's buildings.

    Queen's campus map is currently located at http://queensu.ca/maps
    '''

    host = 'http://www.queensu.ca'
    scraper = Scraper()

    @staticmethod
    def scrape(location='./dumps/buildings'):
        '''Update database records for buildings scraper'''

        print("Starting buildings scrape")

        campuses = Buildings._get_campuses('campusmap/overall')

        for campus in campuses:
            campus_name = Buildings._get_campus_name(campus.text)
            campus_url = urljoin(Buildings.host, campus.find('a')['href'])
            buildings = Buildings._get_buildings(campus_url)

            for building in buildings:
                try:
                    building_href = building['href']
                    building_param = building_href.split('=')[1]

                    print('Building Parameter: {}'.format(building_param))

                    soup = Buildings.scraper.http_request(
                        campus_url, params={'mapquery': building_param}
                    )

                    building_data = Buildings._parse_building_data(
                        soup, campus_name, building_href)

                    if building_data:
                        Buildings.scraper.write_data(
                            building_data, building_param, location)

                except Exception as ex:
                    Buildings.scraper.handle_error(ex, 'scrape')

                Buildings.scraper.wait()

    @staticmethod
    def _get_campuses(relative_url):
        '''
        Get list of campus URLs as BeautifulSoup HTML tags

        Returns:
            List[bs4.element.Tag]
        '''

        campus_overall_url = urljoin(Buildings.host, relative_url)
        soup = Buildings.scraper.http_request(campus_overall_url)
        campuses = soup.find_all('p', 'overall-label')

        return campuses

    @staticmethod
    def _get_campus_name(campus):
        return campus.strip().lower().replace('the ', '').split(' campus')[0]

    @staticmethod
    def _get_buildings(campus_url):
        '''
        Get list of relative building URLs as BeautifulSoup HTML tags

        Returns:
            List[bs4.element.Tag]
        '''

        # pull campus name from relative url, such as /campusmap/west,
        # which splits by '/' and grab the last value
        campus_name = campus_url.split('/')[-1]

        print('Campus: {campus}'.format(campus=campus_name.upper()))
        print('========================\n')

        campus_url = urljoin(Buildings.host, campus_url)
        soup = Buildings.scraper.http_request(campus_url)
        campus_map = soup.find('map')
        buildings = campus_map.find_all('area')

        return buildings

    @staticmethod
    def _parse_building_data(soup, campus, building_href):
        '''
        Parse data from building tags

        Returns:
            Object
        '''

        def parse_label(label, is_address=False):
            if label:
                label_text = label.next_sibling
                return label_text.text.strip() if is_address else label_text

            return ''

        def has_accessibility(soup):
            accessible = details.find('img', alt=re.compile('Accessibility'))
            return True if accessible else False

        def get_polygon(coords, campus):
            '''convert polygon coords into tuple of integer pairs'''
            polygon = []

            # normalize Isabel building coordinate format
            if campus == 'isabel':
                coords = re.sub(r'([0-9]+),([0-9]+)', r' \1,\2', coords).strip()

            coords = coords.replace('\r\n', ' ').replace('\n', ' ').split(', ')

            for coords_str in coords:
                x, y = coords_str.split(',')
                polygon.append([int(x), int(y)])

            return polygon

        # Parsing campus map tag
        campus_map = soup.find('map')
        building = campus_map.find('area', href=building_href)

        # Parsing building sidebar info
        details = soup.find('div', class_='building-details')
        address_label = details.find('span', text=re.compile('Address'))
        code_label = details.find('span', text=re.compile('Building Code'))

        # Actual data
        param = building_param = building_href.split('=')[1]
        name = soup.find('div', class_='title').text.strip()
        code = parse_label(code_label)
        address = parse_label(address_label, is_address=True)
        is_accessible = has_accessibility(details)
        latitude, longitude = get_building_coords(address)
        polygon = get_polygon(building['coords'], campus)

        data = {
            '_parameter': param,
            'code': code,
            'accessibility': is_accessible,
            'name': name,
            'address': address,
            'latitude': latitude,
            'longitude': longitude,
            'campus': campus,
            'polygon': polygon,
        }

        return data
