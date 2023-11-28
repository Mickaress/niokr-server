from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils.db import connect_db
from utils.request import required_fields

vacancy = Blueprint('vacancy', __name__)


@vacancy.route("/api/vacancies")
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
@vacancy.route("/api/vacancy/<int:vacancy_id>")
def get_vacancy(vacancy_id):
    with connect_db() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM vacancies WHERE is_accept = 1 AND id = ?", (vacancy_id,))
        vacancy = cursor.fetchone()

    if vacancy:
        return jsonify({'vacancy': vacancy})
    else:
        return jsonify({'message': 'Вакансия не найдена'}), 404


# Создание вакансии
@vacancy.route("/api/supervisor/vacancy", methods=['POST'])
@jwt_required()
def create_vacancy():
    with connect_db() as connection:
        cursor = connection.cursor()

        # Получение данных о пользователе
        user_id = get_jwt_identity()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        existing_user = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        user = {columns[i]: existing_user[i] for i in range(len(columns))}

        data = request.get_json()

        # Проверка на необходимые поля
        error_response = required_fields(data, ['title', 'description', 'date_start', 'date_end', 'conditions', 'duties', 'requirements', 'project_id', 'skills'])
        if error_response:
            return jsonify({'error': error_response}), 400

        # Получение данных о НИОКР
        cursor.execute("SELECT * FROM projects WHERE id = ?", (data['project_id'],))
        project_data = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        project = {columns[i]: project_data[i] for i in range(len(columns))}

        # Проверка на доступ к выбранному НИОКР
        if project['supervisor_id'] != user['id']:
            return jsonify({'error': 'Нет доступа'}), 400

        # Добавление вакансии в БД
        cursor.execute("INSERT INTO vacancies (title, description, date_start, date_end, conditions, duties, requirements, project_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (data['title'], data['description'], data['date_start'], data['date_end'], data['conditions'], data['duties'], data['requirements'], data['project_id']))

        # Получение id только что добавленной вакансии
        vacancy_id = cursor.lastrowid

        # Добавление навыков в таблицу vacancy_skill
        for skill_id in data['skills']:
            cursor.execute("INSERT INTO vacancy_skill (vacancy_id, skill_id) VALUES (?, ?)", (vacancy_id, skill_id))

        return jsonify({'message': 'Вакансия добавлена'})


# Рассмотрение вакансий
@vacancy.route("/api/admin/vacancy", methods=['GET', 'PATCH'])
@jwt_required()
def admin_vacancy():
    with connect_db() as connection:
        cursor = connection.cursor()

        # Получение данных о пользователе
        user_id = get_jwt_identity()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        existing_user = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        user = {columns[i]: existing_user[i] for i in range(len(columns))}

        # Только админ может одобрять/отклонять вакансии
        if user['role_id'] != 4:
            return jsonify({'message': 'Нет доступа'})

        if request.method == 'GET':
            cursor.execute("SELECT * FROM vacancies WHERE is_accept is null")

            columns = [column[0] for column in cursor.description]
            vacancies = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return jsonify({'vacancies': vacancies})
        else:
            data = request.get_json()

            # Проверка на наличие нужных полей в теле запроса
            error_response = required_fields(data, ['id', 'is_accept'])
            if error_response:
                return jsonify({'error': error_response}), 400

            # Обновление статуса вакансии
            cursor.execute("UPDATE vacancies SET is_accept = ? WHERE id = ?", (data['is_accept'], data['id'],))

            return jsonify({'message': 'Вакансия обновлена'})
