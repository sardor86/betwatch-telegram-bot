import json
from datetime import datetime, timezone, timedelta

import requests

from tgbot.config import BASE_URL


class BetWatchParser:
    """
    class BetWatchParser get information from BetWatch site

    class has some filters for parser and  filters is set in __init__.py
    using this filter method get_matches will return runner
    but you can change this filter while this class work
    """

    def __init__(self, pre_matches: bool = False, live_matches: bool = False,
                 from_price: int = 0, to_price: int = 99999,
                 from_percentage: int = 0, to_percentage: int = 100,
                 from_coefficient: int = 0, to_coefficient: int = 99999,
                 from_time_1: int = 0, to_time_1: int = 45,
                 from_time_2: int = 45, to_time_2: int = 90,
                 block_list: list = []) -> None:
        """
        magical method __init__ set filters and mainly attributes

        :param pre_matches: bool, default False use for pre matches
        :param live_matches: bool, default False use for live matches
        :param from_price: start price
        :param to_price: end price
        :param from_percentage: start percentage
        :param to_percentage: end percentage
        :param from_coefficient: start coefficient
        :param to_coefficient: end coefficient
        :param from_time_1: start time 1
        :param to_time_1: end time 1
        :param from_time_2: start time 2
        :param to_time_2: end time 2
        :param block_list: block list for filters

        self.session is used for connect to server and get data from server
        self.matches is used for save match data
        """

        if block_list is None:
            block_list = []
        self.session = requests.Session()
        self.matches: dict = {}

        self.pre_matches = pre_matches
        self.live_matches = live_matches

        self.from_price = from_price
        self.to_price = to_price

        self.from_percentage = from_percentage
        self.to_percentage = to_percentage

        self.from_coefficient = from_coefficient
        self.to_coefficient = to_coefficient

        self.from_time_1 = from_time_1
        self.to_time_1 = to_time_1

        self.from_time_2 = from_time_2
        self.to_time_2 = to_time_2

        self.block_list = block_list

    @staticmethod
    def translate_money(money: int) -> int:
        """
        this method translate money to understandable number for server
        this is static method because this methode only translate money to number and return it
        this method doesn't save data to self
        but this method round the number and server can send incorrect data and so you should check the data from server
        :param money: money in euro
        :return: understandable number for server
        """
        if money <= 10:
            return money

        len_number = 10 ** (len(str(money)) - 1)

        last_number = (money - len_number) // (len_number * 0.5)

        result = 11 + last_number
        while len_number != 10:
            result += 18
            len_number /= 10

        return int(result)

    async def get_match_runners(self, mach_id) -> list:
        """
        this method get runners use match id and return it
        this method check the runners use some filters such as price, coefficient and percentage

        if runners is unsuitable, this method will send empty list
        :param mach_id: match id
        :return: runners list
        """
        result = []
        data = json.loads(self.session.get(f'{BASE_URL}/{mach_id}',
                                           headers={'X-Requested-With': 'XMLHttpRequest'}).text)['i']
        for runner_id in data:
            for runner_data in data[runner_id]:
                if runner_data[0] in self.block_list:
                    continue
                if not runner_data[4]:
                    continue
                runner_result = {
                    'name': f'{runner_data[0]} || {runner_data[1]}',
                    'price': runner_data[2],
                    'coefficient': float(runner_data[3]),
                    'percentage': int(100 * (runner_data[2] / runner_data[4]))
                }

                if not (self.from_price <= runner_result['price'] <= self.to_price):
                    continue
                if not (self.from_coefficient <= runner_result['coefficient'] <= self.to_coefficient):
                    continue
                if not (self.from_percentage <= runner_result['percentage'] <= self.to_percentage):
                    continue
                result.append(runner_result)

        return result

    async def get_matches(self, country: str = '', step: int = 1) -> None:
        """
        this method get matches from server with some filters and save it to self.matches
        """
        date = datetime.now().strftime("%Y-%m-%d")
        matches_data = self.session.get(f'{BASE_URL}/football/getMoney?choice=&'
                                        f'date={date}&'
                                        f'live_only={str(self.live_matches).lower()}&'
                                        f'prematch_only={str(self.pre_matches).lower()}&'
                                        'not_countries=&'
                                        'not_leagues=&'
                                        'settings_order=score&'
                                        f'country={country}&'
                                        'league=&'
                                        'filtering=true&'
                                        'utc=3&'
                                        f'step={step}&'
                                        f'min_vol={self.translate_money(self.from_price)}&'
                                        f'max_vol={self.translate_money(self.to_price)}&'
                                        f'min_percent={self.from_percentage}&'
                                        f'max_percent={self.to_percentage}&'
                                        'min_odd=0&'
                                        'max_odd=349', headers={'X-Requested-With': 'XMLHttpRequest'})
        matches_list = json.loads(matches_data.text)['data']
        for match in matches_list:
            result = {
                'id': match['e'],
                'match': match['m'],
                'average': match['vm'],
            }
            if match['n'] in self.block_list:
                continue
            if match['l']:
                result['type'] = 'live'
                live_data = json.loads(self.session.get(f'https://betwatch.fr/live?live={result["id"]}').text)
                if not (str(result['id']) in live_data):
                    continue
                live_data = live_data[str(result['id'])]
                result['time'] = live_data[0]
                result['score'] = live_data[1]

                if live_data[0] == 'HT':
                    result['time'] = 45
                else:
                    if '+' in live_data[0]:
                        result['time'] = sum([int(numbers) for numbers in live_data[0].split('+')])
                    else:
                        result['time'] = int(live_data[0])

                if not (self.from_time_1 <= result['time'] <= self.to_time_1 or
                        self.from_time_2 <= result['time'] <= self.to_time_2):
                    continue
            else:
                result['type'] = 'pre-match'
                if not (match['ce'].split('T')[0] == date):
                    continue
                result['time'] = match['ce'].split('T')[0][:-1]
            result['runners'] = await self.get_match_runners(result['id'])
            if not result['runners']:
                continue
            self.matches[match['e']] = result

    async def get_all_matches(self):
        await self.get_matches(step=5)
        await self.get_matches('International', step=5)
