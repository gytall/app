import requests
import json

# Базовый URL для API hh.ru
BASE_URL = "https://api.hh.ru/vacancies"

# Параметры запроса
params = {
    'text': 'Python',  # Пример: поиск вакансий с упоминанием "Python"
    'area': 1,  # Пример: Москва
    'per_page': 10,  # Количество вакансий на странице (максимум 100)
    'page': 0  # Номер страницы (начинается с 0)
}

def get_vacancies(url, params):
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code)
        return None

def parse_vacancies(data):
    vacancies = []
    for item in data['items']:
        vacancy = {
            'name': item['name'],
            'description': item['snippet']['responsibility'],
            'salary': item['salary'],
            'location': item['area']['name'],
            'company': item['employer']['name'],
            'url': item['alternate_url']
        }
        vacancies.append(vacancy)
    return vacancies

def main():
    data = get_vacancies(BASE_URL, params)
    if data:
        vacancies = parse_vacancies(data)
        # Печать информации о вакансиях
        for v in vacancies:
            print(f"Название: {v['name']}")
            print(f"Описание: {v['description']}")
            print(f"Зарплата: {v['salary']}")
            print(f"Местоположение: {v['location']}")
            print(f"Компания: {v['company']}")
            print(f"URL: {v['url']}")
            print("\n" + "-"*40 + "\n")

if __name__ == "__main__":
    main()