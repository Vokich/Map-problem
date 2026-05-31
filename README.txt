=== КАРТА ГОРОДСКИХ ПРОБЛЕМ ===

1. Установка библиотек:
   pip install -r requirements.txt

2. Создание миграции БД:
   python manage.py makemigrations

3. Применение миграций БД:
   python manage.py migrate

4. Создание суперпользователя (опционально):
   python manage.py createsuperuser

5. Запуск сервера:
   python manage.py runserver

6. Открыть в браузере:
   http://127.0.0.1:8000

Для работы карты требуется интернет (подключается Leaflet.js, OpenStreetMap).
Для загрузки изображений нужна папка images (создаётся автоматически).

Версия: 1.0