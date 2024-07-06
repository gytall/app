from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import chardet
import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app)  # Разрешает CORS для всех маршрутов

BASE_URL = "https://api.hh.ru/vacancies"
AREAS_URL = "https://api.hh.ru/areas"
MAX_WORKERS = 10

DB_HOST = 'localhost'
DB_PORT = 5433
DB_NAME = 'database'
DB_USER = 'user'
DB_PASS = '12345'

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS vacancies (
        id VARCHAR(255) PRIMARY KEY,
        name TEXT,
        key_skills TEXT,
        experience TEXT,
        salary TEXT,
        location TEXT,
        company TEXT,
        url TEXT
    )
    '''
    cursor = conn.cursor()
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    return conn

def save_vacancies(vacancies):
    conn = get_db_connection()
    cursor = conn.cursor()
    for vacancy in vacancies:
        cursor.execute('''
            INSERT INTO vacancies (id, name, key_skills, experience, salary, location, company, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            key_skills = EXCLUDED.key_skills,
            experience = EXCLUDED.experience,
            salary = EXCLUDED.salary,
            location = EXCLUDED.location,
            company = EXCLUDED.company,
            url = EXCLUDED.url
        ''', (vacancy['id'], vacancy['name'], vacancy['key_skills'], vacancy['experience'], vacancy['salary'], vacancy['location'], vacancy['company'], vacancy['url']))
    conn.commit()
    cursor.close()
    conn.close()

def get_vacancies_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, key_skills, experience, salary, location, company, url FROM vacancies')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    vacancies = []
    for row in rows:
        vacancy = {
            'id': row[0],
            'name': row[1],
            'key_skills': row[2],
            'experience': row[3],
            'salary': row[4],
            'location': row[5],
            'company': row[6],
            'url': row[7]
        }
        vacancies.append(vacancy)
    
    return vacancies

def get_area_id(area_name):
    response = requests.get(AREAS_URL)
    if response.status_code == 200:
        areas = response.json()
        for country in areas:
            for region in country['areas']:
                if region['name'].lower() == area_name.lower():
                    return region['id']
                for city in region['areas']:
                    if city['name'].lower() == area_name.lower():
                        return city['id']
    return None

def get_vacancies(url, params, total_vacancies=20):
    all_vacancies = []
    current_page = params.get('page', 0)

    def fetch_page(page):
        params['page'] = page
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = decode_response(response.content)
            vacancies = parse_vacancies(data)
            return vacancies
        else:
            return []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {executor.submit(fetch_page, page): page for page in range(current_page, current_page + MAX_WORKERS)}
        for future in as_completed(future_to_page):
            page_vacancies = future.result()
            all_vacancies.extend(page_vacancies)
            if len(all_vacancies) >= total_vacancies:
                break

    return list(all_vacancies)[:total_vacancies]

def decode_response(content):
    try:
        return content.decode('utf-8')
    except UnicodeDecodeError:
        result = chardet.detect(content)
        encoding = result['encoding']
        return content.decode(encoding)

def parse_vacancies(data):
    vacancies = []
    json_data = json.loads(data)
    for item in json_data['items']:
        salary = get_salary(item['salary'])
        if not salary:
            continue
        vacancy_id = item['id']
        key_skills = get_key_skills(vacancy_id)
        if not key_skills:
            key_skills = item['snippet']['requirement'] if item['snippet']['requirement'] else 'No key skills or requirements provided'
        experience = item['experience']['name'] if item['experience'] else 'Опыт работы не важен'
        vacancy = {
            'id': item['id'],
            'name': item['name'],
            'key_skills': key_skills,
            'experience': experience,
            'salary': salary,
            'location': item['area']['name'],
            'company': item['employer']['name'],
            'url': item['alternate_url']
        }
        vacancies.append(vacancy)
    return vacancies

def get_key_skills(vacancy_id):
    response = requests.get(f"{BASE_URL}/{vacancy_id}")
    if response.status_code == 200:
        data = decode_response(response.content)
        json_data = json.loads(data)
        key_skills = [skill['name'] for skill in json_data.get('key_skills', [])]
        return ', '.join(key_skills)
    return ""

def get_salary(salary):
    if not salary or salary.get('currency') != 'RUR':
        return ""
    if salary['from'] and salary['to']:
        return f"{salary['from']} - {salary['to']} {salary['currency']}"
    if salary['from']:
        return f"от {salary['from']} {salary['currency']}"
    if salary['to']:
        return f"до {salary['to']} {salary['currency']}"
    return ""

@app.route('/', methods=['GET'])
def index():
    return 'Hello'

@app.route('/vacancies', methods=['GET'])
def get_all_vacancies():
    # Сначала получаем данные из базы данных
    vacancies = get_vacancies_from_db()
    
    # Если в базе данных нет данных, то получаем данные из API и сохраняем их в базу данных
    if not vacancies:
        total_vacancies = request.args.get('total', default=50, type=int)
        vacancies = get_vacancies(BASE_URL, {'per_page': total_vacancies}, total_vacancies)
        save_vacancies(vacancies)
    
    return jsonify(vacancies)

@app.route('/vacancies_from_api', methods=['GET'])
def get_vacancies_from_api():
    page = request.args.get('page', default=0, type=int)
    per_page = request.args.get('per_page', default=20, type=int)
    params = {'page': page, 'per_page': per_page}
    vacancies = get_vacancies(BASE_URL, params, per_page)
    return jsonify(vacancies)

if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        print('Successfully connected to the database')
        conn.close()
    app.run(host='0.0.0.0', port=5000, debug=True)