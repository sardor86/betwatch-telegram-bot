import json
from datetime import datetime
import logging

import pytz
import requests
from bs4 import BeautifulSoup

from tgbot.config import BASE_URL

logger = logging.getLogger(__name__)


class BetWatchParser:
    """
    class BetWatchParser get information from BetWatch site

    class has some filters for parser and  filters is set in __init__.py
    using this filter method get_matches will return runner
    but you can change this filter while this class work
    """
    def __init__(self, from_price: int = 0, to_price: int = 99999,
                 from_percentage: int = 0, to_percentage: int = 100,
                 from_coefficient: int = 0, to_coefficient: int = 99999,
                 from_time: int = 0, up_time: int = 150,
                 block_list: list = [],
                 online_matches: bool = False, pre_matches: bool = False) -> None:
        """
        magical method __init__ set filters and mainly attributes

        :param from_price: start price
        :param to_price: end price
        :param from_percentage: start percentage
        :param to_percentage: end percentage
        :param from_coefficient: start coefficient
        :param to_coefficient: end coefficient
        :param from_time: start time
        :param up_time: end time
        :param block_list: block list for filters

        self.session is used for connect to server and get data from server
        self.matches is used for save match data such as name: id_match
        """

        self.session = requests.Session()
        self.online_matches = online_matches
        self.pre_matches = pre_matches
        self.matches: dict = {}

        self.from_price = from_price
        self.to_price = to_price

        self.from_percentage = from_percentage
        self.to_percentage = to_percentage

        self.from_coefficient = from_coefficient
        self.to_coefficient = to_coefficient

        self.from_time = from_time
        self.up_time = up_time

        self.block_list = block_list

        logger.info('BetWatchParser __init__ set filters and mainly attributes')

    async def get_matches_list(self, step: int = 1, country: str = '') -> None:
        """
        this method get data from BetWatch site and save it to self.matches
        """
        html = self.session.get(f'{BASE_URL}/football/getMain?'
                                f'date={datetime.now().date()}&'
                                f'live_only={str(self.online_matches).lower()}&'
                                f'prematch_only={str(self.pre_matches).lower()}&'
                                'not_countries=&'
                                'not_leagues=&'
                                'settings_order=country&'
                                f'country={country}&'
                                'league=&'
                                'utc=5&'
                                f'step={step}')
        data = json.loads(html.text)
        for match in data['data']:
            self.matches[match['m']] = match['e']
        logger.info('BetWatchParser get_matches_list has got matches info and save it to self.matches')

    async def get_all_matches(self) -> None:
        """
        this method clear self.matches and
        get all matches(ordinary and International matches) data from BetWatch site
        and save match name and id to self.matches
        """
        self.matches = {}
        for step in range(1, 4):
            await self.get_matches_list(step=step)
            await self.get_matches_list(step=step, country='International')
        logger.info('has got all matches list and save it to self.matches')

    async def get_match_time(self, match: str, match_type: str) -> dict:
        """
        this method get main information about match
        such as name, type, and time if type is live, this method will return score to
        """
        logger.info('BetWatchParser get_math_main_info has called')
        result: dict = {
            'time': ''
        }

        logger.info('starting get match time')

        if match_type == 'live':
            match_info = json.loads(self.session.get(f'https://betwatch.fr/live?live={self.matches[match]}').text)
            if match_info[0] == 'HT':
                result['time'] = 45
            else:
                result['time'] = sum([int(match_time_number) for match_time_number in match_info[0].split('+')])
            result['type'] = 'live'
            result['score'] = match_info[1]
            return result

        match_time = json.loads(self.session.get(f'{BASE_URL}/football/{self.matches[match]}',
                                                 headers={'X-Requested-With': 'XMLHttpRequest'}).text)['ce']

        date_utc = datetime.strptime(match_time, "%Y-%m-%dT%H:%M:%SZ")
        your_timezone = pytz.timezone('Europe/Moscow')

        match_time_local = date_utc.replace(tzinfo=pytz.utc).astimezone(your_timezone)
        result['time'] = match_time_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        return result

    async def get_match_info(self, match: str) -> dict:
        """
        this method get runner info of match and return it
        this method use filters that has set in __init__ magical method

        if method can`t find this match,
        it will return dict with name not found and another parameters with not found

        :param match: name of match
        :return: runner info of match
        """
        logger.info('get_match_info has called')

        result: dict = {
            'name': match,
            'type': '',
            'time': None,
            'runners': []
        }

        logger.info('checking match')
        html = self.session.get(f'{BASE_URL}/{self.matches[match]}')

        if html.status_code == 404:
            logger.warning('match not found')
            return {
                'name': 'not found',
                'type': 'not found',
                'time': 'not found',
                'runners': []
            }

        logger.info('soup is being created')
        soup = BeautifulSoup(html.text, 'html.parser')

        logger.info('get match type')
        if soup.find_all('div', class_='header-button'):
            result['type'] = 'live'
        else:
            result['type'] = 'pre-match'

        logger.info('getting math time')
        match_time = await self.get_match_time(match, result['type'])

        logger.info('checking the time')
        result['time'] = match_time['time']
        if result['type'] == 'live':
            if not (self.from_time <= match_time['time'] <= self.up_time):
                result['runners'] = [],
                return result
            result['score'] = match_time['score']

        logger.info('getting match runners')
        for info in soup.find_all('div', class_='match-issues'):
            for runner in info.find_all('div', class_='match-runner'):
                name = info.find('div', class_='match-issue').text

                if name in self.block_list:
                    continue

                runner_name = runner.find('div', class_='runner-large').text
                price = int(''.join(runner.find('div', class_='volume').text[:-1].split(',')))
                if not (self.from_price <= price <= self.to_price):
                    continue

                try:
                    percentage = int(runner.find('div', class_='runner-container').find_all('div')[2].text[:-1])
                except ValueError:
                    continue
                if not (self.from_percentage <= percentage <= self.to_percentage):
                    continue

                try:
                    coefficient = float(runner.find('div', class_='odd').text)
                except ValueError:
                    continue
                if not (self.from_coefficient <= coefficient <= self.to_coefficient):
                    continue

                result['runners'].append({
                    'name': f'{name} || { runner_name }',
                    'price': price,
                    'percentage': percentage,
                    'coefficient': coefficient
                })
        return result
