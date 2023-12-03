from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils.db import connect_db

project = Blueprint('project', __name__)


# Получение списка НИОКР
@project.route("/api/projects")
def get_projects():
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            # Фильтр по странице
            page = int(request.args.get('page', 1))
            items_per_page = 3
            offset = (page - 1) * items_per_page
            limit = items_per_page

            # Общее количество записей для пагинации на фронте
            cursor.execute("SELECT COUNT(*) FROM projects")
            amount = cursor.fetchone()[0]

            # Получение списка НИОКР
            cursor.execute("SELECT * FROM projects LIMIT ? OFFSET ?", (limit, offset))
            columns = [column[0] for column in cursor.description]
            projects = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify({'projects': projects, 'amount': amount})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Получение одного НИОКР
@project.route("/api/project/<int:project_id>")
def get_project(project_id):
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            project_data = cursor.fetchone()

            if not project_data:
                return jsonify({'error': 'НИОКР не найден'}), 404

            columns = [column[0] for column in cursor.description]
            project = {columns[i]: project_data[i] for i in range(len(columns))}

            return jsonify({'project': project})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Получение списка вакансий НИОКР
@project.route("/api/project/<int:project_id>/vacancies")
def get_project_vacancies(project_id):
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            project = cursor.fetchone()

            if not project:
                return jsonify({'error': 'НИОКР не найден'}), 404

            cursor.execute("SELECT * FROM vacancies WHERE project_id = ?", (project_id,))

            columns = [column[0] for column in cursor.description]
            vacancies = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return jsonify({'vacancies': vacancies})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Получение списка НИОКР руководителя
@project.route("/api/supervisor/projects")
@jwt_required()
def get_supervisor_projects():
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            user_id = get_jwt_identity()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            existing_user = cursor.fetchone()
            columns = [column[0] for column in cursor.description]
            user = {columns[i]: existing_user[i] for i in range(len(columns))}

            if user['role_id'] != 3:
                return jsonify({'error': 'Нет доступа'}), 403

            cursor.execute("SELECT * FROM projects WHERE supervisor_id = ?", (user['id'],))

            columns = [column[0] for column in cursor.description]
            projects = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return jsonify({'projects': projects})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500
