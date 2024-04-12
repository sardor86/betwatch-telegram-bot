import json
from datetime import datetime

import pytz
import requests
from bs4 import BeautifulSoup

from tgbot.config import BASE_URL


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
                 online_matches: bool = True, pre_matches: bool = True) -> None:
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

    async def get_match_main_info(self, match: str) -> dict:
        """
        this method get main information about match
        such as name, type, and time if type is live, this method will return score to
        """
        result = {
            'name': match,
            'time': '',
            'type': ''
        }
        match_info = json.loads(self.session.get(f'https://betwatch.fr/live?live={self.matches[match]}').text)
        if not match_info:
            result['type'] = 'pre-match'
            match_time = json.loads(self.session.get(f'{BASE_URL}/football/{self.matches[match]}',
                                                     headers={'X-Requested-With': 'XMLHttpRequest'}).text)['ce']

            date_utc = datetime.strptime(match_time, "%Y-%m-%dT%H:%M:%SZ")
            your_timezone = pytz.timezone('Europe/Moscow')

            match_time_local = date_utc.replace(tzinfo=pytz.utc).astimezone(your_timezone)
            result['time'] = match_time_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')
            return result

        if match_info[0] == 'HT':
            result['time'] = 45
        else:
            result['time'] = sum([int(match_time_number) for match_time_number in match_info[0].split('+')])
        result['type'] = 'live'
        result['score'] = match_info[1]

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
        html = self.session.get(f'{BASE_URL}/{self.matches[match]}')

        if html.status_code == 404:
            return {
                'name': 'not found',
                'type': 'not found',
                'time': 'not found',
                'runners': []
            }

        result = await self.get_match_main_info(match)
        if self.from_time <= result['time'] <= self.up_time:
            result['runners'] = [],
            return result

        soup = BeautifulSoup(html.text, 'html.parser')

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
