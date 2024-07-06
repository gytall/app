Веб-приложение для парсинга вакансий с hh.ru
Описание

Данное веб-приложение на базе Flask и React позволяет парсить вакансии с сайта hh.ru и сохранять их в базу данных PostgreSQL. Приложение предоставляет REST API для получения информации о вакансиях и позволяет выполнять поиск по различным критериям.
Функциональные возможности

    Парсинг вакансий с hh.ru и сохранение их в базе данных.
    Возможность просмотра вакансий в веб-интерфейсе.
    Асинхронная загрузка данных с использованием ThreadPoolExecutor.
    Обработка CORS-запросов.

Технологии

    Backend: Flask, psycopg2, requests
    Frontend: React
    База данных: PostgreSQL
    Docker

Установка и запуск

Клонировать репозиторий

    git clone https://github.com/gytall/app.git
    

Предварительные требования

    Docker
    Docker Compose

Использование, сборка и запуск контейнеров Docker

    docker-compose build
    docker-compose up

Запуск frontend 

    npm run dev

Запуск backend

    python main.py



