from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils.db import connect_db
from utils.request import required_fields

vacancy = Blueprint('vacancy', __name__)


# Получение списка вакансий
@vacancy.route("/api/vacancies")
def get_vacancies():
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            # Фильтр по странице
            page = int(request.args.get('page', 1))
            items_per_page = 3
            offset = (page - 1) * items_per_page
            limit = items_per_page

            # Фильтр по названию
            title = str(request.args.get('title', ''))

            # Фильтр по оплате
            payment = str(request.args.get('payment'))
            payment_condition = ""
            if payment:
                if payment == 'true':
                    payment_condition = f" AND salary > 0"
                if payment == 'false':
                    payment_condition = f" AND salary = 0"

            # Фильтр по навыкам
            skills = request.args.getlist('skills')
            skill_conditions = ""
            if skills:
                placeholders = ', '.join('?' for _ in skills)
                skill_conditions = f" AND vacancies.id IN (SELECT vacancy_id FROM vacancy_skill WHERE skill_id IN ({placeholders}))"

            # Общее количество записей для пагинации на фронте
            count_query = f"SELECT COUNT(*) FROM vacancies WHERE is_accept = 1 AND LOWER(title) LIKE LOWER(?) {payment_condition} {skill_conditions}"
            cursor.execute(count_query, (f"%{title}%", *skills))
            amount = cursor.fetchone()[0]

            # Получение списка вакансий
            query = f"SELECT * FROM vacancies WHERE is_accept = 1 AND LOWER(title) LIKE LOWER(?) {payment_condition} {skill_conditions} LIMIT ? OFFSET ?"
            cursor.execute(query, (f"%{title}%", *skills, limit, offset))

            columns = [column[0] for column in cursor.description]
            vacancies = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify({'vacancies': vacancies, 'amount': amount})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Получение одной вакансии
@vacancy.route("/api/vacancy/<int:vacancy_id>")
def get_vacancy(vacancy_id):
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM vacancies WHERE is_accept = 1 AND id = ?", (vacancy_id,))
            vacancy_data = cursor.fetchone()

            if not vacancy_data:
                return jsonify({'error': 'Вакансия не найдена'}), 404

            columns = [column[0] for column in cursor.description]
            vacancy = {columns[i]: vacancy_data[i] for i in range(len(columns))}

            return jsonify({'vacancy': vacancy})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Создание вакансии
@vacancy.route("/api/supervisor/vacancy", methods=['POST'])
@jwt_required()
def create_vacancy():
    try:
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
            if not project_data:
                return jsonify({'error': 'НИОКР не найден'}), 404
            columns = [column[0] for column in cursor.description]
            project = {columns[i]: project_data[i] for i in range(len(columns))}

            # Проверка на доступ к выбранному НИОКР
            if project['supervisor_id'] != user['id']:
                return jsonify({'error': 'Нет доступа'}), 403

            # Добавление вакансии в БД
            cursor.execute("INSERT INTO vacancies (title, description, date_start, date_end, conditions, duties, requirements, project_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (data['title'], data['description'], data['date_start'], data['date_end'], data['conditions'], data['duties'], data['requirements'], data['project_id']))

            # Получение id только что добавленной вакансии
            vacancy_id = cursor.lastrowid

            # Добавление навыков в таблицу vacancy_skill
            for skill_id in data['skills']:
                cursor.execute("INSERT INTO vacancy_skill (vacancy_id, skill_id) VALUES (?, ?)", (vacancy_id, skill_id))

            return jsonify({'message': 'Вакансия добавлена'})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Рассмотрение вакансий
@vacancy.route("/api/admin/vacancy", methods=['GET', 'PATCH'])
@jwt_required()
def admin_vacancy():
    try:
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
                return jsonify({'error': 'Нет доступа'}), 403

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

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500
