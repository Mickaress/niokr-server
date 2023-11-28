# niokr-server
Серверная часть проекта "Ярмарка НИОКР"

# Общие роуты:
1. Получение списка вакансий (сделано) /api/vacancies
2. Получение одной вакансии (сделано) /api/vacancy/:id
3. Получение списка НИОКР (сделано) /api/projects
4. Получение одного НИОКР (сделано) /api/project/:id
5. Получение списка вакансий НИОКР (сделано) /api/project/:id/vacancies
6. Получение данных для регистрации (сделано) /api/user/props
7. Регистрация (сделано) /api/user/registration
8. Авторизация (сделано) /api/user/auth
# Соискатель
1. Отклик на вакансию (сделано) /api/candidate/response/:id
2. Просмотр своих откликов (сделано) /api/candidate/responses
3. Предложение новых навыков (сделано) /api/skill
4. Изменение своих навыков (сделано) /api/candidate/skills
# Руководитель
1. Просмотр списка своих НИОКР (сделано) /api/supervisor/projects
2. Просмотр списка вакансий в своих НИОКР (не сделано) 
3. Просмотр списка откликов на вакансию в своем НИОКР (сделано)  /api/supervisor/vacancy/responses/:id
4. Создание вакансии (сделано) /api/supervisor/vacancy
5. Предложение новых навыков (сделано) /api/skill
6. Модерация откликов (сделано) /api/supervisor/response/:id
# Администратор
1. Добавление навыков (сделано) /api/skill
2. Рассмотрение предложенных навыков (сделано) /api/admin/skill
   3. Рассмотрение предложенных вакансий (сделано) /api/admin/vacancy