import re
from datetime import datetime


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
