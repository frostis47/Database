import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class HeadHunterAPI:

    def __init__(self):
        self.base_url = "https://api.hh.ru/"
        self.per_page = 100

    def get_employers(self, query, area=113, page=0):

        url = f"{self.base_url}employers"
        params = {
            "text": query,
            "page": page,
            "per_page": self.per_page
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()['items']
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при получении работодателей (query={query}, area={area}, page={page}): {e}")
            return []

    def get_employer_by_id(self, employer_id):

        url = f"{self.base_url}employers/{employer_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при получении информации о работодателе (ID={employer_id}): {e}")
            return None

    def get_vacancies(self, employer_id, page=0):

        url = f"{self.base_url}vacancies"
        params = {
            "employer_id": employer_id,
            "page": page,
            "per_page": self.per_page
        }
        try:
            response = requests.get(url, params=params)
            logging.info(f"Request URL: {response.url}")
            response.raise_for_status()
            return response.json()['items']
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при получении вакансий (employer_id={employer_id}, page={page}): {e}")
            return []