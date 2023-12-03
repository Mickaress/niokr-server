from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from utils.db import connect_db
from utils.request import is_valid_email, required_fields, is_valid_date, is_valid_phone, is_valid_fio

user = Blueprint('user', __name__)


# Получение полей для регистрации (руководителя и админа убираем из ролей, так как их нельзя регистрировать)
@user.route("/api/user/props")
def get_user_props():
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            # Получение ролей
            cursor.execute("SELECT * FROM roles WHERE id IN (1, 2)")
            columns = [column[0] for column in cursor.description]
            roles = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Получение групп
            cursor.execute("SELECT * FROM groups")
            columns = [column[0] for column in cursor.description]
            groups = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Получение институтов
            cursor.execute("SELECT * FROM institutes")
            columns = [column[0] for column in cursor.description]
            institutes = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Получение кафедр
            cursor.execute("SELECT * FROM departments")
            columns = [column[0] for column in cursor.description]
            departments = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Получение должностей
            cursor.execute("SELECT * FROM posts")
            columns = [column[0] for column in cursor.description]
            posts = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return jsonify({'roles': roles, 'groups': groups, 'institutes': institutes, 'departments': departments,
                            'posts': posts})

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Регистрация
@user.route("/api/user/registration", methods=['POST'])
def registration():
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            data = request.get_json()

            # Проверка на необходимые общие поля
            error_response = required_fields(data, ['email', 'password', 'fio', 'role', 'phone'])
            if error_response:
                return jsonify({'error': error_response}), 400

            # Валидация общих полей
            if not is_valid_email(data['email']):
                return jsonify({'error': 'Неправильный формат почты'}), 400
            if not is_valid_fio(data['fio']):
                return jsonify({'error': 'Неправильный формат ФИО'}), 400
            if not is_valid_phone(data['phone']):
                return jsonify({'error': 'Неправильный формат номера телефона'}), 400

            role = data['role']

            # Нельзя регистрироваться как администратор или руководитель
            if role in [3, 4]:
                return jsonify({'error': 'Нельзя регистрироваться как администратор или руководитель'}), 403

            # Проверка на уже существующий адрес почты
            cursor.execute("SELECT * FROM users WHERE email = ?", (data['email'],))
            existing_email = cursor.fetchone()
            if existing_email:
                return jsonify({'error': 'Пользователь с данной почтой уже существует'}), 409

            # Проверка на уже существующий номер телефона
            cursor.execute("SELECT * FROM users WHERE phone = ?", (data['phone'],))
            existing_phone = cursor.fetchone()
            if existing_phone:
                return jsonify({'error': 'Пользователь с данным номером уже существует'}), 409

            # Регистрация студента-соискателя
            if role == 1:
                # Проверка на необходимые поля для студента-соискателя
                error_response = required_fields(data, ['group', 'institute', 'departament', 'birthday'])
                if error_response:
                    return jsonify({'error': error_response}), 400

                # Проверка на существование зависимостей в других таблицах
                cursor.execute("SELECT * FROM groups WHERE id = ?", (data['group'],))
                existing_group = cursor.fetchone()
                if not existing_group:
                    return jsonify({'error': 'Выбранной группы не существует'}), 404

                cursor.execute("SELECT * FROM institutes WHERE id = ?", (data['institute'],))
                existing_institute = cursor.fetchone()
                if not existing_institute:
                    return jsonify({'error': 'Выбранного института не существует'}), 404

                cursor.execute("SELECT * FROM departments WHERE id = ?", (data['departament'],))
                existing_departament = cursor.fetchone()
                if not existing_departament:
                    return jsonify({'error': 'Выбранной кафедры не существует'}), 404

                # Валидация даты рождения
                if not is_valid_date(data['birthday']):
                    return jsonify({'error': 'Неправильный формат даты'}), 400

                # Хеширование пароля
                password = generate_password_hash(data['password'])

                # Создание записи о пользователе в БД
                cursor.execute(
                    "INSERT INTO users (email, password, fio, role_id, group_id, institute_id, departament_id, phone, birthday) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (data['email'], password, data['fio'], data['role'], data['group'], data['institute'],
                     data['departament'], data['phone'], data['birthday']))

                return jsonify({'message': 'Успешная регистрация'})

            # Регистрация сотрудника-соискателя
            if role == 2:
                # Проверка на необходимые поля для сотрудника-соискателя
                error_response = required_fields(data, ['departament', 'post'])
                if error_response:
                    return jsonify({'error': error_response}), 400

                # Проверка на существование зависимостей в других таблицах
                cursor.execute("SELECT * FROM departments WHERE id = ?", (data['departament'],))
                existing_departament = cursor.fetchone()
                if not existing_departament:
                    return jsonify({'error': 'Выбранной кафедры не существует'}), 404

                cursor.execute("SELECT * FROM posts WHERE id = ?", (data['post'],))
                existing_post = cursor.fetchone()
                if not existing_post:
                    return jsonify({'error': 'Выбранной должности не существует'}), 404

                # Хеширование пароля
                password = generate_password_hash(data['password'])

                # Создание записи о пользователе в БД
                cursor.execute(
                    "INSERT INTO users (email, password, fio, role_id, departament_id, post_id, phone) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (data['email'], password, data['fio'], data['role'], data['departament'], data['post'],
                     data['phone']))

                return jsonify({'message': 'Успешная регистрация'})

            return jsonify({'error': 'Указана несуществующая роль'}), 400

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Авторизация
@user.route("/api/user/auth", methods=['POST'])
def auth():
    try:
        with connect_db() as connection:
            cursor = connection.cursor()

            data = request.get_json()

            # Проверка на необходимые поля
            error_response = required_fields(data, ['email', 'password'])
            if error_response:
                return jsonify({'error': error_response}), 400

            # Валидация почты
            if not is_valid_email(data['email']):
                return jsonify({'error': 'Неправильный формат почты'}), 400

            # Поиск пользователя
            cursor.execute("SELECT * FROM users WHERE email = ?", (data['email'],))
            existing_user = cursor.fetchone()
            if not existing_user:
                return jsonify({'error': 'Пользователь не существует'}), 404
            columns = [column[0] for column in cursor.description]
            user = {columns[i]: existing_user[i] for i in range(len(columns))}

            # Проверка пароля
            if not check_password_hash(user['password'], data['password']):
                return jsonify({'error': 'Неправильный пароль'}), 401

            access_token = create_access_token(identity=user['id'])

            return jsonify(access_token=access_token)

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500
