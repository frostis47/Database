import psycopg2

class DBManager:


    def __init__(self, dbname, user, password, host='localhost', port='5432'):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None

    def connect(self):

        try:
            self.conn = psycopg2.connect(dbname=self.dbname, user=self.user,
                                         password=self.password, host=self.host, port=self.port)
            self.conn.autocommit = True
            return True
        except psycopg2.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return False

    def disconnect(self):

        if self.conn:
            try:
                self.conn.close()
                self.conn = None
                print("Успешно отключено от базы данных.")
            except psycopg2.Error as e:
                print(f"Ошибка при отключении от базы данных: {e}")

    def create_tables(self):

        if not self.conn:
            print("Необходимо подключиться к базе данных перед созданием таблиц.")
            return

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    DROP TABLE IF EXISTS vacancies;
                    DROP TABLE IF EXISTS companies;
                """)

                cur.execute("""
                                CREATE TABLE companies (
                                    company_id INTEGER PRIMARY KEY,
                                    company_name VARCHAR(255) NOT NULL,
                                    description TEXT,
                                    employees_count INTEGER,
                                    company_url TEXT
                                );
                            """)

                cur.execute("""
                    CREATE TABLE vacancies (
                        vacancy_id SERIAL PRIMARY KEY,
                        company_id INTEGER REFERENCES companies(company_id),
                        vacancy_name VARCHAR(255) NOT NULL,
                        salary_from INTEGER,
                        salary_to INTEGER,
                        currency VARCHAR(50),
                        vacancy_url TEXT,
                        description TEXT
                    );
                """)
            print("Таблицы успешно созданы.")
        except psycopg2.Error as e:
            print(f"Ошибка при создании таблиц: {e}")

    def save_data_to_db(self, companies, vacancies):
        """
        Сохраняет данные о компаниях и вакансиях в базу данных.

        Args:
            companies (list): Список словарей с информацией о компаниях.
            vacancies (list): Список словарей с информацией о вакансиях.
        """
        if not self.conn:
            print("Необходимо подключиться к базе данных перед сохранением данных.")
            return

        try:
            with self.conn.cursor() as cur:
                # Сохраняем компании
                for company in companies:
                    cur.execute("""
                        INSERT INTO companies (company_id, company_name, description, employees_count, company_url)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (company_id) DO NOTHING
                    """, (
                    company['id'], company['name'], company.get('description', ''), company.get('employees_count', 0),
                    company.get('company_url', '')))

                # Сохраняем вакансии
                for vacancy in vacancies:
                    salary_from = vacancy['salary']['from'] if vacancy['salary'] else None
                    salary_to = vacancy['salary']['to'] if vacancy['salary'] else None
                    currency = vacancy['salary']['currency'] if vacancy['salary'] else None

                    cur.execute("""
                        INSERT INTO vacancies (company_id, vacancy_name, salary_from, salary_to, currency, vacancy_url, description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (vacancy['employer']['id'], vacancy['name'], salary_from, salary_to, currency,
                          vacancy['alternate_url'], vacancy['snippet']['requirement']))
            print("Данные успешно сохранены в базу данных.")
        except psycopg2.Error as e:
            print(f"Ошибка при сохранении данных в базу данных: {e}")

    def get_companies_and_vacancies_count(self):

        if not self.conn:
            print("Необходимо подключиться к базе данных.")
            return []

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT c.company_name, COUNT(v.vacancy_id)
                    FROM companies c
                    LEFT JOIN vacancies v ON c.company_id = v.company_id
                    GROUP BY c.company_name
                    ORDER BY c.company_name
                """)
                return cur.fetchall()
        except psycopg2.Error as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return []

    def get_all_vacancies(self):

        if not self.conn:
            print("Необходимо подключиться к базе данных.")
            return []

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT c.company_name, v.vacancy_name, v.salary_from, v.salary_to, v.vacancy_url
                    FROM vacancies v
                    JOIN companies c ON v.company_id = c.company_id
                """)
                return cur.fetchall()
        except psycopg2.Error as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return []

    def get_avg_salary(self):

        if not self.conn:
            print("Необходимо подключиться к базе данных.")
            return None

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT AVG((salary_from + salary_to) / 2)
                    FROM vacancies
                    WHERE salary_from IS NOT NULL AND salary_to IS NOT NULL
                """)
                result = cur.fetchone()[0]
                return result if result is not None else 0
        except psycopg2.Error as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return None

    def get_vacancies_with_higher_salary(self):

        if not self.conn:
            print("Необходимо подключиться к базе данных.")
            return []

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT vacancy_name, salary_from, salary_to, vacancy_url
                    FROM vacancies
                    WHERE (salary_from + salary_to) / 2 > (SELECT AVG((salary_from + salary_to) / 2) FROM vacancies WHERE salary_from IS NOT NULL AND salary_to IS NOT NULL)
                    AND salary_from IS NOT NULL AND salary_to IS NOT NULL
                """)
                return cur.fetchall()
        except psycopg2.Error as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return []

    def get_vacancies_with_keyword(self, keyword):

        if not self.conn:
            print("Необходимо подключиться к базе данных.")
            return []

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT v.vacancy_name, c.company_name, v.salary_from, v.salary_to, v.vacancy_url
                    FROM vacancies v
                    JOIN companies c ON v.company_id = c.company_id
                    WHERE v.vacancy_name ILIKE %s
                """, ('%' + keyword + '%',))
                return cur.fetchall()
        except psycopg2.Error as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return []