from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils.db import connect_db
from utils.request import required_fields

skill = Blueprint('skill', __name__)


# Добавление навыков
@skill.route("/api/skill", methods=['POST'])
@jwt_required()
def add_skill():
    with connect_db() as connection:
        cursor = connection.cursor()

        # Получение данных о пользователе
        user_id = get_jwt_identity()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        existing_user = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        user = {columns[i]: existing_user[i] for i in range(len(columns))}

        data = request.get_json()

        # Проверка на наличие названия навыка в теле запроса
        error_response = required_fields(data, ['name'])
        if error_response:
            return jsonify({'error': error_response}), 400

        # Админ может сразу создать одобренный навык
        if user['role_id'] == 4:
            cursor.execute("INSERT INTO skills (name, is_accept) VALUES (?, ?)", (data['name'], 1))

            return jsonify({'message': 'Навык добавлен'})

        # Другие роли могут добавить навыки только после рассмотрения администратором
        cursor.execute("INSERT INTO skills (name) VALUES (?)", (data['name'],))

        return jsonify({'message': 'Навык на рассмотрение'})


# Рассмотрение навыков
@skill.route("/api/admin/skill", methods=['GET', 'PATCH'])
@jwt_required()
def admin_skill():
    with connect_db() as connection:
        cursor = connection.cursor()

        # Получение данных о пользователе
        user_id = get_jwt_identity()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        existing_user = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        user = {columns[i]: existing_user[i] for i in range(len(columns))}

        # Только админ может одобрять/отклонять навыки
        if user['role_id'] != 4:
            return jsonify({'message': 'Нет доступа'})

        if request.method == 'GET':
            cursor.execute("SELECT * FROM skills WHERE is_accept is null")

            columns = [column[0] for column in cursor.description]
            skills = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return jsonify({'skills': skills})
        else:
            data = request.get_json()

            # Проверка на наличие нужных полей в теле запроса
            error_response = required_fields(data, ['id', 'is_accept'])
            if error_response:
                return jsonify({'error': error_response}), 400

            # Обновление статуса навыка
            cursor.execute("UPDATE skills SET is_accept = ? WHERE id = ?", (data['is_accept'], data['id'],))

            return jsonify({'message': 'Навык обновлен'})


# Получение списка навыков
@skill.route("/api/skills")
@jwt_required()
def get_skills():
    with connect_db() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM skills WHERE is_accept is 1")

        columns = [column[0] for column in cursor.description]
        skills = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify({'skills': skills})


# Навыки соискателя
@skill.route("/api/candidate/skills", methods=['GET', 'PUT'])
@jwt_required()
def candidate_skills():
    with connect_db() as connection:
        cursor = connection.cursor()

        # Получение данных о пользователе
        user_id = get_jwt_identity()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        existing_user = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        user = {columns[i]: existing_user[i] for i in range(len(columns))}

        if user['role'] not in [1, 2]:
            return jsonify({'error': 'Навыки могут менять только соискатели'}), 400

        if request.method == 'GET':
            cursor.execute("SELECT * FROM user_skill WHERE user_id == ?", (user['id'],))

            columns = [column[0] for column in cursor.description]
            skills = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return jsonify({'skills': skills})
        else:
            data = request.get_json()

            # Проверка на наличие массива навыков теле запроса
            error_response = required_fields(data, ['skills'])
            if error_response:
                return jsonify({'error': 'В теле нет массива навыков'}), 400

            cursor.execute('''
                        DELETE FROM user_skill
                        WHERE user_id = ? AND skill_id NOT IN ({})
                    '''.format(','.join(['?'] * len(data['skills']))), [user['id']] + data['skills'])

            for skill_id in data['skills']:
                cursor.execute('''
                            INSERT INTO user_skill (user_id, skill_id)
                            VALUES (?, ?)
                            ON CONFLICT(user_id, skill_id) DO NOTHING
                        ''', (user['id'], skill_id))
