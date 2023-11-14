from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)


def connect_db():
    return sqlite3.connect('database.db')


# Получение списка вакансий
@app.route("/api/vacancies")
def get_vacancies():
    with connect_db() as connection:
        cursor = connection.cursor()

        # Общее количество записей для пагинации на фронте
        cursor.execute("SELECT COUNT(*) FROM vacancies WHERE is_accept = 1")
        amount = cursor.fetchone()[0]

        # Получение списка вакансий на выбранной странице
        page = int(request.args.get('page', 1))
        items_per_page = 3
        offset = (page - 1) * items_per_page
        limit = items_per_page

        cursor.execute("SELECT * FROM vacancies WHERE is_accept = 1 LIMIT ? OFFSET ?", (limit, offset))

        columns = [column[0] for column in cursor.description]
        vacancies = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return jsonify({'vacancies': vacancies, 'amount': amount})


# Получение одной вакансии
@app.route("/api/vacancy/<int:vacancy_id>")
def get_vacancy(vacancy_id):
    with connect_db() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM vacancies WHERE is_accept = 1 AND id = ?", (vacancy_id,))
        vacancy = cursor.fetchone()

    if vacancy:
        return jsonify({'vacancy': vacancy})
    else:
        return jsonify({'message': 'Вакансия не найдена'}), 404


# Получение списка НИОКР
@app.route("/api/projects")
def get_projects():
    with connect_db() as connection:
        cursor = connection.cursor()

        # Общее количество записей для пагинации на фронте
        cursor.execute("SELECT COUNT(*) FROM projects")
        amount = cursor.fetchone()[0]

        # Получение списка НИОКР на выбранной странице
        page = int(request.args.get('page', 1))
        items_per_page = 3
        offset = (page - 1) * items_per_page
        limit = items_per_page

        cursor.execute("SELECT * FROM projects LIMIT ? OFFSET ?", (limit, offset))

        columns = [column[0] for column in cursor.description]
        projects = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return jsonify({'projects': projects, 'amount': amount})


# Получение одного НИОКР
@app.route("/api/project/<int:project_id>")
def get_project(project_id):
    with connect_db() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()

    if project:
        return jsonify({'project': project})
    else:
        return jsonify({'message': 'НИОКР не найден'}), 404


if __name__ == '__main__':
    app.run(debug=True)
