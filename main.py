import requests
import json
import chardet
from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app)

# Базовый URL для API hh.ru
BASE_URL = "https://api.hh.ru/vacancies"
AREAS_URL = "https://api.hh.ru/areas"
MAX_WORKERS = 10  # Количество параллельных потоков

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
    current_page = 0

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
        future_to_page = {executor.submit(fetch_page, page): page for page in range(total_vacancies)}
        for future in as_completed(future_to_page):
            page_vacancies = future.result()
            all_vacancies.extend(page_vacancies)
            if len(all_vacancies) >= total_vacancies:
                break

    return all_vacancies[:total_vacancies]

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
        vacancy_id = item['id']
        key_skills = get_key_skills(vacancy_id)
        if not key_skills:
            key_skills = item['snippet']['requirement'] if item['snippet']['requirement'] else 'No key skills or requirements provided'
        salary = get_salary(item['salary'])
        experience = item['experience']['name'] if item['experience'] else 'Опыт работы не важен'
        vacancy = {
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
    if not salary:
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
    total_vacancies = request.args.get('total', default=50, type=int)
    vacancies = get_vacancies(BASE_URL, {'per_page': total_vacancies}, total_vacancies)
    return jsonify(vacancies)

if __name__ == "__main__":
    app.run(debug=True)