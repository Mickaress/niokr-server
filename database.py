import sqlite3

connection = sqlite3.connect('database.db')
cursor = connection.cursor()

# Пользователи могут иметь разные роли (соискатель-студент, соискатель-сотрудник ИрНИТУ, руководитель НИОКР и модератор). У разных ролей разные поля, поэтому было решено сделать единную таблицу для всех, где ненужные поля будут пустыми.
# Общие поля: почта, пароль, ФИО.
# Уникальные поля соискателя-студента: группа, специальность, институт, кафедра, телефон, дата рождения (для выявления молодых ученых управление научной деятельности).
# Уникальные поля соискателя-сотрудника ИрНИТУ: должность, кафедра, телефон.
# Уникальные поля руководителя НИОКР: телефон.
# Уникальные поля модератора: нет.
# P.S. В настоящем приложение авторизация будет проходить через кампус, для этой работы будет использоваться обычная авторизация/регистрация по email и password.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        fio TEXT NOT NULL,
        role_id INTEGER REFERENCES roles(id) NOT NULL,
        group_id INTEGER REFERENCES groups(id) DEFAULT NULL,
        institute_id INTEGER REFERENCES institutes(id) DEFAULT NULL,
        departament_id INTEGER REFERENCES departments(id) DEFAULT NULL,
        post_id INTEGER REFERENCES posts(id) DEFAULT NULL,
        birthday TEXT DEFAULT NULL,
        phone TEXT DEFAULT NULL
    )
''')

# Таблица ролей
cursor.execute('''
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
	)
''')

# Добавление всех ролей
to_insert = ['student', 'employee', 'supervisor', 'admin']
data_to_insert = [(data,) for data in to_insert]
cursor.executemany("INSERT INTO roles (name) VALUES (?)", data_to_insert)

# Таблица групп
cursor.execute('''
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
	)
''')

# В настоящем приложении данные о группе будут приходить с кампуса и их никак нельзя будет изменить. Здесь для примера я просто добавлю пару групп в таблицу.
to_insert = ['АСУб', 'ИСТб', 'ЭВМб']
data_to_insert = [(data,) for data in to_insert]
cursor.executemany("INSERT INTO groups (name) VALUES (?)", data_to_insert)

# Таблица институтов
cursor.execute('''
    CREATE TABLE IF NOT EXISTS institutes (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
	)
''')

# В настоящем приложении данные об институте будут приходить с кампуса и их никак нельзя будет изменить. Здесь для примера я просто добавлю пару институтов в таблицу.
to_insert = ['Институт информационных технологий и анализа данных', 'Институт высоких технологий', 'Байкальский институт БРИКС']
data_to_insert = [(data,) for data in to_insert]
cursor.executemany("INSERT INTO institutes (name) VALUES (?)", data_to_insert)

# Таблица кафедр
cursor.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
	)
''')

# В настоящем приложении данные о кафедре будут приходить с кампуса и их никак нельзя будет изменить. Здесь для примера я просто добавлю пару кафедр в таблицу.
to_insert = ['ИрНИТУ', 'Кафедра высоких технологий', 'Кафедра энергетики']
data_to_insert = [(data,) for data in to_insert]
cursor.executemany("INSERT INTO departments (name) VALUES (?)", data_to_insert)

# Таблица должностей
cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
	)
''')

# В настоящем приложении данные о должности будут приходить с кампуса и их никак нельзя будет изменить. Здесь для примера я просто добавлю пару должностей в таблицу.
to_insert = ['Профессор', 'Доцент', 'Ассистент']
data_to_insert = [(data,) for data in to_insert]
cursor.executemany("INSERT INTO posts (name) VALUES (?)", data_to_insert)

# Таблица НИОКР
cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        salary INTEGER DEFAULT 0,
        date_start TEXT NOT NULL,
        date_end TEXT NOT NULL,
        conditions TEXT NOT NULL,
        goals TEXT NOT NULL,
        supervisor_id INTEGER REFERENCES users(id) NOT NULL
    )
''')

# Таблица вакансий. is_accept для модератора. Руководитель НИОКР создает вакансию. Она проходит модерацию перед публикацией. NULL - на модерации, 0 - отклонена, 1 - одобрена.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS vacancies (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        date_start TEXT NOT NULL,
        date_end TEXT NOT NULL,
        conditions TEXT NOT NULL,
        duties TEXT NOT NULL,
        requirements TEXT NOT NULL,
        project_id INTEGER REFERENCES projects(id) NOT NULL,
        is_accept INTEGER CHECK (is_accept IN (0, 1)) DEFAULT NULL,
        salary INTEGER DEFAULT 0
    )
''')

# Таблица откликов. is_accept для руководителя НИОКР. Соискатель оставляет отклик на вакансию и видит его статус. NULL - не просмотрен, 0 - отклонен, 1 - одобрен.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) NOT NULL,
        vacancy_id INTEGER REFERENCES vacancies(id) NOT NULL,
        is_accept INTEGER CHECK (is_accept IN (0, 1)) DEFAULT NULL
    )
''')


# Таблица навыков. is_accept для модератора. Руководитель НИОКР или соискатели могут создать заявку на добавление навыка в БД. NULL - на модерации, 0 - отклонена, 1 - одобрена.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        is_accept INTEGER CHECK (is_accept IN (0, 1)) DEFAULT NULL
    )
''')

# Таблица для связи многие ко многим между вакансиями и навыками
cursor.execute('''
    CREATE TABLE IF NOT EXISTS vacancy_skill (
        id INTEGER PRIMARY KEY,
        vacancy_id INTEGER REFERENCES vacancies(id) NOT NULL,
        skill_id INTEGER REFERENCES skills(id) NOT NULL
    )
''')

# Таблица для связи многие ко многим между соискателями и навыками
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_skill (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) NOT NULL,
        skill_id INTEGER REFERENCES skills(id) NOT NULL
    )
''')

connection.commit()
connection.close()
