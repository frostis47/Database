from api.headhunter_api import HeadHunterAPI
from db.db_manager import DBManager

import logging
from utils import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    db_manager = DBManager(config.DB_NAME, config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_PORT)
    if not db_manager.connect():
        logging.error("Не удалось подключиться к базе данных.")
        exit()

    hh_api = HeadHunterAPI()

    company_names = config.COMPANY_NAMES
    companies_data = []
    vacancies_data = []

    for company_name in company_names:
        try:
            employers = hh_api.get_employers(company_name)
            if employers:
                employer = employers[0]
                employer_data = hh_api.get_employer_by_id(employer['id'])
                if employer_data:
                    logging.info(f"Получены полные данные о работодателе: {employer_data['name']} (ID: {employer_data['id']})")


                    company = {
                        'id': employer['id'],
                        'name': employer_data['name'],
                        'description': employer_data.get('description', ''),
                        'employees_count': employer_data.get('employees_count', 0),
                        'company_url': employer_data.get('alternate_url', '')
                    }
                    companies_data.append(company)

                    page = 0
                    max_pages = 5

                    while page < max_pages:
                        try:
                            vacancies = hh_api.get_vacancies(employer['id'], page)

                            if not vacancies:
                                logging.info(f"API вернул пустой список вакансий для {company_name} на странице {page}.")
                                break

                            for vacancy in vacancies:
                                logging.info(f"Обрабатываем вакансию: {vacancy['name']} (ID работодателя: {vacancy['employer']['id']})")
                                vacancies_data.append(vacancy)

                            page += 1
                        except Exception as e:
                            logging.error(f"Ошибка при получении вакансий (страница {page}) для компании {company_name} (ID {employer['id']}): {e}")
                            break
                else:
                    logging.warning(f"Не удалось получить полные данные о работодателе для компании {company_name} (ID {employer['id']})")
            else:
                logging.warning(f"Не удалось найти работодателя для компании {company_name}")
        except Exception as e:
            logging.error(f"Общая ошибка при обработке компании {company_name}: {e}")

        vacancies_count = len(vacancies_data)
        logging.info(f"Получено {vacancies_count} вакансий для компании {company_name}")

    db_manager.create_tables()

    try:
        logging.info(f"Сохраняем {len(companies_data)} компаний и {len(vacancies_data)} вакансий в базу данных.")
        db_manager.save_data_to_db(companies_data, vacancies_data)
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных в базу данных: {e}")

    print("\n--- Компании и количество вакансий ---")
    companies_vacancies_count = db_manager.get_companies_and_vacancies_count()
    for company, count in companies_vacancies_count:
        print(f"{company}: {count} вакансий")

    db_manager.disconnect()