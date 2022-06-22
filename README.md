
Сервер развёрнут по адресу https://regulations-1972.usr.yandex-academy.ru

Документация к API представлена в файле `openapi.json`.

Развёртывание приложения
========================
Приложение упаковано в docker контейнеры. Для его развёртывания достаточно запустить контейнеры.
Для развертывания необхоним docker-compose.

### Сборка и запуск контейнера
    docker-compose -f docker-compose.prod.yaml up --build -d

### Применение миграций
    docker-compose -f docker-compose.prod.yaml exec web python manage.py migrate

#### Проверка создания бд
Проверить создана ли база данных можно с помощью комманд:
    
    docker-compose exec db psql --username=hello_django --dbname=postgres
    \l
В списке БД должна быть `hello_django_prod`



Тесты
========================
Для запуска тестов необходимо проверить разрешения юзера БД
    
    docker-compose exec db psql --username=hello_django --dbname=postgres
    \du+

Необходимо разрешение `Create DB`

### Запуск тестов

Для запуска тестов выполните команду:
    
    docker-compose -f docker-compose.prod.yaml exec web python manage.py test .
