# Foodgram

Foodgram — веб-приложение для публикации рецептов. Пользователи могут создавать рецепты, добавлять их в избранное, подписываться на авторов и формировать список покупок на основе выбранных рецептов.

Проект состоит из Django REST API, React frontend, PostgreSQL, Nginx gateway и Docker Compose окружения для запуска в production.

## Адрес проекта

Проект доступен по адресу:

[Foodgram](https://foodgrams.2bd.net/)

Админ-зона:

[Панель администратора](https://foodgrams.2bd.net/admin/)

API:

[API Foodgram](https://foodgrams.2bd.net/api/)

Документация API:

[Документация API](https://foodgrams.2bd.net/api/docs/)

## Возможности

- регистрация и авторизация пользователей;
- создание, редактирование и удаление рецептов;
- загрузка изображений для рецептов;
- фильтрация рецептов по тегам, автору, избранному и списку покупок;
- добавление рецептов в избранное;
- добавление рецептов в список покупок;
- скачивание списка покупок в `.txt`;
- подписка на авторов;
- короткая ссылка на рецепт;
- импорт продуктов и тегов через management-команды;
- административная панель для управления данными.

## Технологии

Backend:

- Python 3.11
- Django
- Django REST Framework
- Djoser
- PostgreSQL
- Gunicorn

Frontend:

- React
- JavaScript

Инфраструктура:

- Docker
- Docker Compose
- Nginx
- GitHub Actions
- Docker Hub

## Структура backend-приложения

Основная доменная логика находится в приложении `recipes`.

API-слой вынесен в приложение `api`:

- сериализаторы;
- viewsets;
- permissions;
- filters;
- urls.

Данные пользователей, подписок, рецептов, продуктов, избранного и списка покупок хранятся в доменных моделях проекта.

Внешний endpoint для продуктов оставлен как `/api/ingredients/`, чтобы сохранить совместимость с frontend и API-контрактом проекта.

## Основные API endpoints

```text
/api/users/                         # пользователи
/api/auth/token/login/              # получение токена
/api/auth/token/logout/             # удаление токена
/api/tags/                          # теги
/api/ingredients/                   # продукты/ингредиенты
/api/recipes/                       # рецепты
/api/recipes/{id}/favorite/         # избранное
/api/recipes/{id}/shopping_cart/    # список покупок
/api/recipes/download_shopping_cart/ # скачать список покупок
/api/recipes/{id}/get-link/         # короткая ссылка
/s/{id}/                            # переход по короткой ссылке
```

## Переменные окружения

Для запуска нужен файл `.env`.

Пример:

```env
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432

SECRET_KEY=django-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,foodgrams.2bd.net
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1,https://foodgrams.2bd.net

DOCKERHUB_USERNAME=dmitryborisov04
```

## Локальный запуск через Docker

Клонируйте репозиторий:

```bash
git clone https://github.com/DmitryBorisov04/foodgram.git
```

Перейдите в папку проекта:

```bash
cd foodgram
```

Создайте файл `.env` в корне проекта и заполните его по примеру из раздела «Переменные окружения».

Запустите контейнеры:

```bash
docker compose up -d --build
```

Выполните миграции:

```bash
docker compose exec backend python manage.py migrate
```

Импортируйте продукты и теги:

```bash
docker compose exec backend python manage.py import_products
docker compose exec backend python manage.py import_tags
```

Соберите статику Django:

```bash
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend sh -c 'rm -rf /backend_static/* && cp -r /app/collected_static/. /backend_static/'
```

Создайте суперпользователя:

```bash
docker compose exec backend python manage.py createsuperuser
```

Проект будет доступен локально:

[Главная страница](http://localhost/)

[Панель администратора](http://localhost/admin/)

[API](http://localhost/api/)

[Документация API](http://localhost/api/docs/)

## Production-запуск

На сервере используется `docker-compose.production.yml`.

Запуск:

```bash
sudo docker compose -f docker-compose.production.yml up -d
```

Миграции:

```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```

Импорт данных:

```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_products
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_tags
```

Сборка Django static:

```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
sudo docker compose -f docker-compose.production.yml exec backend sh -c 'rm -rf /backend_static/* && cp -r /app/collected_static/. /backend_static/'
```

## Импорт данных

В проекте есть две management-команды:

```bash
python manage.py import_products
python manage.py import_tags
```

`import_products` загружает продукты из:

```text
/app/data/ingredients.json
```

`import_tags` загружает теги из:

```text
/app/data/tags.json
```

Команды можно запускать повторно. Уже существующие записи будут пропущены.

## GitHub Actions

Для автоматического деплоя через GitHub Actions используются следующие secrets:

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN

HOST
USER
SSH_KEY

SECRET_KEY
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS

POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD

TELEGRAM_TO
TELEGRAM_TOKEN
```

Docker-образы:

```text
dmitryborisov04/foodgram_backend:latest
dmitryborisov04/foodgram_frontend:latest
dmitryborisov04/foodgram_gateway:latest
```

## Администрирование

В админ-панели доступны основные сущности проекта:

- пользователи;
- рецепты;
- продукты;
- теги;
- подписки;
- избранное;
- список покупок.

Для входа нужен суперпользователь:

```bash
python manage.py createsuperuser
```

## Автор

Дмитрий Борисов

[GitHub](https://github.com/DmitryBorisov04)

[Telegram](https://t.me/mbbbellini)