from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils.db import connect_db
from utils.request import required_fields

response = Blueprint('response', __name__)


# Отклик на вакансию
@response.route("/api/candidate/response/<int:vacancy_id>", methods=['POST'])
@jwt_required()
def vacancy_response(vacancy_id):
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            # Получение данных о пользователе
            user_id = get_jwt_identity()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            existing_user = cursor.fetchone()
            columns = [column[0] for column in cursor.description]
            user = {columns[i]: existing_user[i] for i in range(len(columns))}

            if user['role_id'] not in [1, 2]:
                return jsonify({'error': 'Нет доступа'}), 403

            cursor.execute("SELECT * FROM vacancies WHERE id = ?", (vacancy_id,))
            existing_vacancy = cursor.fetchone()
            if not existing_vacancy:
                return jsonify({'error': 'Выбранной вакансии не существует'}), 404

            cursor.execute("SELECT * FROM responses WHERE user_id = ? AND vacancy_id = ?", (user['id'], vacancy_id,))
            existing_response = cursor.fetchone()
            if existing_response:
                return jsonify({'error': 'Вы уже откликнулись на эту вакансию'}), 409

            cursor.execute("INSERT INTO responses (user_id, vacancy_id) VALUES (?, ?)", (user['id'], vacancy_id,))

            return jsonify({'message': 'Вы откликнулись на вакансию'})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Список откликов соискателя
@response.route("/api/candidate/responses")
@jwt_required()
def get_candidate_responses():
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            # Получение данных о пользователе
            user_id = get_jwt_identity()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            existing_user = cursor.fetchone()
            columns = [column[0] for column in cursor.description]
            user = {columns[i]: existing_user[i] for i in range(len(columns))}

            cursor.execute("SELECT * FROM responses WHERE user_id = ?", (user['id'],))
            columns = [column[0] for column in cursor.description]
            responses = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return jsonify({'responses': responses})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Получение списка откликов на вакансию
@response.route("/api/supervisor/vacancy/responses/<int:vacancy_id>")
@jwt_required()
def get_vacancy_responses(vacancy_id):
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            # Получение данных о пользователе
            user_id = get_jwt_identity()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            existing_user = cursor.fetchone()
            columns = [column[0] for column in cursor.description]
            user = {columns[i]: existing_user[i] for i in range(len(columns))}

            # Получение вакансии
            cursor.execute("SELECT * FROM vacancies WHERE id = ?", (vacancy_id,))
            vacancy_data = cursor.fetchone()

            if not vacancy_data:
                return jsonify({'error': 'Вакансия не найдена'}), 404

            columns = [column[0] for column in cursor.description]
            vacancy = {columns[i]: vacancy_data[i] for i in range(len(columns))}

            # Получение НИОКР
            project_id = vacancy['project_id']
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            project_data = cursor.fetchone()

            if not project_data:
                return jsonify({'error': 'НИОКР не найден'}), 404

            columns = [column[0] for column in cursor.description]
            project = {columns[i]: project_data[i] for i in range(len(columns))}

            # Проверка на доступ
            if project['supervisor_id'] != user['id']:
                return jsonify({'error': 'Нет доступа'}), 403

            # Получение списка откликов
            cursor.execute("SELECT * FROM responses WHERE vacancy_id = ?", (vacancy['id'],))
            columns = [column[0] for column in cursor.description]
            responses = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return jsonify({'responses': responses})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Модерация откликов
@response.route("/api/supervisor/response/<int:response_id>", methods=['PATCH'])
@jwt_required()
def review_response(response_id):
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            # Получение данных о пользователе
            user_id = get_jwt_identity()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            existing_user = cursor.fetchone()
            columns = [column[0] for column in cursor.description]
            user = {columns[i]: existing_user[i] for i in range(len(columns))}

            # Получение данных об отклике
            cursor.execute("SELECT * FROM users WHERE id = ?", (response_id,))
            existing_response = cursor.fetchone()

            if not existing_response:
                return jsonify({'error': 'Отклика не существует'}), 404

            columns = [column[0] for column in cursor.description]
            response = {columns[i]: existing_response[i] for i in range(len(columns))}

            # Получение вакансии
            cursor.execute("SELECT * FROM vacancies WHERE id = ?", (response['vacancy_id'],))
            existing_vacancy = cursor.fetchone()

            if not existing_response:
                return jsonify({'error': 'Отклика не существует'}), 404

            columns = [column[0] for column in cursor.description]
            vacancy = {columns[i]: existing_vacancy[i] for i in range(len(columns))}

            # Получение НИОКР
            cursor.execute("SELECT * FROM projects WHERE id = ?", (vacancy['project_id'],))
            existing_project = cursor.fetchone()

            if not existing_project:
                return jsonify({'error': 'НИОКР не найден'}), 404

            columns = [column[0] for column in cursor.description]
            project = {columns[i]: existing_project[i] for i in range(len(columns))}

            # Проверка на доступ
            if project['supervisor_id'] != user['id']:
                return jsonify({'error': 'Нет доступа'}), 400

            # Получение статуса в теле запроса
            data = request.get_json()

            # Проверка на необходимые поля
            error_response = required_fields(data, ['is_accept'])
            if error_response:
                return jsonify({'error': error_response}), 400

            # Обновление отклика
            cursor.execute("UPDATE responses SET is_accept = ? WHERE id = ?", (data['is_accept'], response_id,))

            return jsonify({'message': 'Данные отклика обновлены'})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500

