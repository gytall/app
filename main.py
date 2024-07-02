import requests
import json
import chardet
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# Базовый URL для API hh.ru
BASE_URL = "https://api.hh.ru/vacancies"
AREAS_URL = "https://api.hh.ru/areas"

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

def get_vacancies(url, params, total_vacancies=50):
    all_vacancies = []
    current_page = 0
    while len(all_vacancies) < total_vacancies:
        params['page'] = current_page
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = chardet.detect(response.content)
            encoding = result['encoding']
            data = response.content.decode(encoding)
            vacancies = parse_vacancies(data)
            all_vacancies.extend(vacancies)
            if len(vacancies) < params['per_page']:  # Если вернулось меньше вакансий, значит, это последняя страница
                break
            current_page += 1
        else:
            print("Error:", response.status_code)
            break
    return all_vacancies[:total_vacancies]

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
        result = chardet.detect(response.content)
        encoding = result['encoding']
        data = response.content.decode(encoding)
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
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    text = request.form.get('text', 'Python')
    area = request.form.get('area', 'Москва')
    per_page = request.form.get('per_page', 20)
    total = request.form.get('total', 50)

    area_id = get_area_id(area)
    if not area_id:
        return jsonify({'error': 'Area not found'})

    params = {
        'text': text,
        'area': area_id,
        'per_page': int(per_page),
        'page': 0
    }

    vacancies = get_vacancies(BASE_URL, params, int(total))
    return jsonify(vacancies)

if __name__ == "__main__":
    app.run(debug=True)
