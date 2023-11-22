from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
jwt = JWTManager(app)


@jwt.unauthorized_loader
def unauthorized_callback(callback):
    return jsonify({'error': 'Нет доступа'}), 401


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

# Получение списка вакансий НИОКР
@app.route("/api/project/vacancies/<int:project_id>")
def get_project_vacancies(project_id):
    with connect_db() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM vacancies WHERE project_id = ?", (project_id,))

        columns = [column[0] for column in cursor.description]
        vacancies = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify({'projects': vacancies})


# Получение полей для регистрации (руководителя и админа убираем из ролей, так как их нельзя регистрировать)
@app.route("/api/user/props")
def get_roles():
    with connect_db() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM roles WHERE id IN (1, 2)")

        columns = [column[0] for column in cursor.description]
        roles = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM groups")

        columns = [column[0] for column in cursor.description]
        groups = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM institutes")

        columns = [column[0] for column in cursor.description]
        institutes = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM departments")

        columns = [column[0] for column in cursor.description]
        departments = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM posts")

        columns = [column[0] for column in cursor.description]
        posts = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify({'roles': roles, 'groups': groups, 'institutes': institutes, 'departments': departments, 'posts': posts})


# Функция на проверку нахождения необходимых полей в теле запроса
def required_fields(data, fields):
    for field in fields:
        if field not in data:
            return f'Не указано обязательное поле: {field}'
    return None


# Валидация электронной почты
def is_valid_email(email):
    # Шаблон для проверки адреса электронной почты
    email_pattern = re.compile(r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$')

    # Сравнение введенной строки с шаблоном
    return bool(re.match(email_pattern, email))


# Валидация ФИО
def is_valid_fio(fio):
    # Шаблон для проверки ФИО
    fio_pattern = re.compile(r'^[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+(?: [А-ЯЁ][а-яё]+)?$')

    # Сравнение введенной строки с шаблоном
    return bool(re.match(fio_pattern, fio))


# Валидация номера телефона
def is_valid_phone(phone):
    # Шаблон для проверки номера телефона
    phone_pattern = re.compile(r'^\+7\d{10}$')

    # Сравнение введенной строки с шаблоном
    return bool(re.match(phone_pattern, phone))


# Валидация даты
def is_valid_date(date):
    try:
        # Преобразование строки в объект datetime
        datetime_object = datetime.strptime(date, '%d.%m.%Y')
        return True
    except ValueError:
        return False


# Регистрация
@app.route("/api/user/registration", methods=['POST'])
def registration():
    with connect_db() as connection:
        cursor = connection.cursor()

        data = request.get_json()

        # Проверка на необходимые общие поля
        error_response = required_fields(data, ['email', 'password', 'fio', 'role', 'phone'])
        print(error_response)
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
            return jsonify({'error': 'Нельзя регистрироваться как администратор или руководитель'}), 400

        # Проверка на уже существующий адрес почты
        cursor.execute("SELECT * FROM users WHERE email = ?", (data['email'],))
        existing_email = cursor.fetchone()
        if existing_email:
            return jsonify({'error': 'Пользователь с данной почтой уже существует'}), 400

        # Проверка на уже существующий номер телефона
        cursor.execute("SELECT * FROM users WHERE phone = ?", (data['phone'],))
        existing_phone = cursor.fetchone()
        if existing_phone:
            return jsonify({'error': 'Пользователь с данным номером уже существует'}), 400

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
                return jsonify({'error': 'Выбранной группы не существует'}), 400

            cursor.execute("SELECT * FROM institutes WHERE id = ?", (data['institute'],))
            existing_institute = cursor.fetchone()
            if not existing_institute:
                return jsonify({'error': 'Выбранного института не существует'}), 400

            cursor.execute("SELECT * FROM departments WHERE id = ?", (data['departament'],))
            existing_departament = cursor.fetchone()
            if not existing_departament:
                return jsonify({'error': 'Выбранной кафедры не существует'}), 400

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
                return jsonify({'error': 'Выбранной кафедры не существует'}), 400

            cursor.execute("SELECT * FROM posts WHERE id = ?", (data['post'],))
            existing_post = cursor.fetchone()
            if not existing_post:
                return jsonify({'error': 'Выбранной должности не существует'}), 400

            # Хеширование пароля
            password = generate_password_hash(data['password'])

            # Создание записи о пользователе в БД
            cursor.execute(
                "INSERT INTO users (email, password, fio, role_id, departament_id, post_id, phone) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (data['email'], password, data['fio'], data['role'], data['departament'], data['post'], data['phone']))

            return jsonify({'message': 'Успешная регистрация'})

        return jsonify({'error': 'Указана несуществующая роль'}), 400


# Авторизация
@app.route("/api/user/auth", methods=['POST'])
def auth():
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

        cursor.execute("SELECT * FROM users WHERE email = ?", (data['email'],))
        existing_user = cursor.fetchone()
        if not existing_user:
            return jsonify({'error': 'Пользователь не существует'}), 400

        columns = [column[0] for column in cursor.description]
        user = {columns[i]: existing_user[i] for i in range(len(columns))}

        if not check_password_hash(user['password'], data['password']):
            return jsonify({'error': 'Неправильный пароль'}), 400

        access_token = create_access_token(identity=user['id'])

        return jsonify(access_token=access_token), 200


# Получение списка НИОКР руководителя
@app.route("/api/supervisor/projects")
@jwt_required()
def get_supervisor_projects():
    with connect_db() as connection:
        cursor = connection.cursor()

        user_id = get_jwt_identity()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        existing_user = cursor.fetchone()

        columns = [column[0] for column in cursor.description]
        user = {columns[i]: existing_user[i] for i in range(len(columns))}

        if user['role_id'] != 3:
            return jsonify({'error': 'Нет доступа'}), 400

        cursor.execute("SELECT * FROM projects WHERE supervisor_id = ?", (user['id'],))

        columns = [column[0] for column in cursor.description]
        projects = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify({'projects': projects})

# Добавление навыков
@app.route("/api/skill", methods=['POST'])
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
@app.route("/api/admin/skill", methods=['GET', 'PATCH'])
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
@app.route("/api/skills")
@jwt_required()
def get_skills():
    with connect_db() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM skills WHERE is_accept is 1")

        columns = [column[0] for column in cursor.description]
        skills = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify({'skills': skills})


# Создание вакансии
@app.route("/api/supervisor/vacancy", methods=['POST'])
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


if __name__ == '__main__':
    app.run(debug=True)
