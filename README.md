# niokr-server
Серверная часть проекта "Ярмарка НИОКР"

# Общие роуты:
1. Получение списка вакансий /api/vacancies
2. Получение одной вакансии /api/vacancy/:id
3. Получение списка НИОКР /api/projects
4. Получение одного НИОКР /api/project/:id
5. Получение списка вакансий НИОКР /api/project/:id/vacancies
6. Получение данных для регистрации /api/user/props
7. Регистрация /api/user/registration
8. Авторизация /api/user/auth
# Соискатель
1. Отклик на вакансию (сделано) /api/candidate/response/:id
2. Просмотр своих откликов (сделано) /api/candidate/responses
3. Предложение новых навыков /api/skill
4. Изменение своих навыков /api/candidate/skills
# Руководитель
1. Просмотр списка своих НИОКР /api/supervisor/projects
2. Просмотр списка откликов на вакансию в своем НИОКР (сделано)  /api/supervisor/vacancy/responses/:id
3. Создание вакансии /api/supervisor/vacancy
4. Предложение новых навыков /api/skill
5. Модерация откликов (сделано) /api/supervisor/response/:id
# Администратор
1. Добавление навыков /api/skill
2. Рассмотрение предложенных навыков /api/admin/skill
3. Рассмотрение предложенных вакансий /api/admin/vacancy