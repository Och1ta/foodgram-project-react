# Продуктовый помощник Foodgram

[![example workflow](https://github.com/Och1ta/foodgram-project-react/actions/workflows/main.yml/badge.svg)](https://github.com/Och1ta/foodgram-project-react/actions/workflows/main.yml)

Продуктовый помощник Foodgram - это сервис, с помощью которого пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд. 

[foodgramfinal.hopto.org](https://foodgramfinal.hopto.org)
```
Для работы проекта был разработан и настроен CI/CD.
```

### Технологи проекта:
```
Python
Django
Django REST framework
Postgres
Docker
Nginx
GitHub Actions
```

### Как запустить проект:
Клонировать репозиторий:
```
git clone https://github.com/Och1ta/foodgram-project-react
```

Для работы workflow необходимо добавить переменные окружения в Secrets GitHub:
```
DOCKER_USERNAME=<имя пользователя DockerHub>
DOCKER_PASSWORD=<пароль DockerHub>

USER=<username для подключения к удаленному серверу>
HOST=<ip-адрес сервера>
SSH_PASSPHRASE=<пароль для сервера (если установлен)>
SSH_KEY=<SSH-ключ (для получения команда: cat ~/.ssh/id_rsa)>

TELEGRAM_TO=<id вашего Телеграм-аккаунта>
TELEGRAM_TOKEN=<Телеграм-токен вашего бота>
```
Пример заполнения .env файла:
```
DB_HOST=db
DB_PORT=5432
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
POSTGRES_DB=foodgram
DATABASES = pg
SECRET_KEY='django-insecure-8jh%pmqs2(k31j$^5u^oa3zefgpdyw&@j_@x$+6a9s64)f$rt$'
ALLOWED_HOSTS='<ваш IP-адрес>, 127.0.0.1, localhost, <ваш домен>'
DEBUG=False
```
Вход на удаленный сервер:
```
ssh <username>@<host>
```

Установка Docker:
```
sudo apt install docker.io
```

Установка Docker-compose:
```
sudo curl -L "https://github.com/docker/compose/releases/download/v2.17.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

Скопируйте файл docker-compose.production.yaml  на сервер

```
scp docker-compose.yaml <username>@<host>:/home/<username>/
```
После успешного деплоя зайдите на боевой сервер и выполните команды:
```
sudo -f docker-compose.production.yml up -d
sudo -f docker-compose.production.yml exec backend python manage.py migrate # примените миграции
sudo -f docker-compose.production.yml exec backend python manage.py collectstatic --no-input # подгрузите статику
sudo -f docker-compose.production.yml exec backend python manage.py load_data # загрузить моковые данные
sudo -f docker-compose.production.yml exec backend python manage.py createsuperuser # создайте суперпользователя

```
### Автор
[Кабнов Антон](https://github.com/Och1ta)
