from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Подключение к базе данных PostgreSQL
def create_db_connection():
    connection = psycopg2.connect(
        database="database",
        user="Ilya",
        password="12345",
        host="localhost",
        port="5432"
    )
    return connection

# Создание таблицы для хранения данных
def create_table(connection):
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_listings (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(255),
                job_title VARCHAR(255),
                skills TEXT,
                work_format VARCHAR(255)
            )
        """)
        connection.commit()

# Маршрут для получения всех записей
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    connection = create_db_connection()
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM job_listings")
        jobs = cursor.fetchall()
    connection.close()
    return jsonify(jobs)

# Маршрут для добавления новой записи
@app.route('/api/jobs', methods=['POST'])
def add_job():
    data = request.json
    connection = create_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO job_listings (full_name, job_title, skills, work_format)
            VALUES (%s, %s, %s, %s)
        """, (data['full_name'], data['job_title'], data['skills'], data['work_format']))
        connection.commit()
    connection.close()
    return jsonify({"message": "Job added successfully"}), 201

# Маршрут для генерации аналитики
@app.route('/api/analytics', methods=['GET'])
def generate_analytics():
    query = """
    SELECT job_title, COUNT(*) as num_listings, AVG(skills_count) as avg_skills
    FROM (
        SELECT job_title, skills, LENGTH(skills) - LENGTH(REPLACE(skills, ',', '')) + 1 as skills_count
        FROM job_listings
    ) as subquery
    GROUP BY job_title
    """
    connection = create_db_connection()
    df = pd.read_sql(query, connection)
    connection.close()
    return df.to_json(orient='records')

if __name__ == "__main__":
    connection = create_db_connection()
    create_table(connection)
    connection.close()
    app.run(debug=True)