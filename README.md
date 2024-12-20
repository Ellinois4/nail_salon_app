# Inventory Management System

## Описание проекта

Проект представляет собой сервис для управления маникюрным салоном.

## Стек технологий

- **Backend**: 
    - Flask (Python Web Framework)
    - PostgreSQL (СУБД)
    - SQLAlchemy (ORM)
    - psycopg2 (PostgreSQL Python клиент)
  
- **Frontend**: 
    - PyQt (для создания графического интерфейса клиентского приложения)

- **Дополнительно**:
    - Requests (для выполнения HTTP запросов)
    - Mermaid/PlantUML для визуализации диаграмм

## Установка

### Требования

1. Python 3.7+
2. PostgreSQL 12+ (или выше)

### Шаги для установки

1. **Клонирование репозитория**

   Склонируйте репозиторий на свой локальный компьютер

2. **Установка зависимостей**

    Установите зависимости проекта с помощью pip:

   ```bash
   pip install -r requirements.txt

3. **Настройка базы данных**

    Создайте базу данных и выполните скрипт для инициализации базы данных.

    Создайте базу данных в PostgreSQL:

    ```sql
     createdb nail_salon_db
   ```
   Настройте подключение в файле back/app.py:
    
    ```python
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/database_name'
   ```
4. **Запустите скрипт инициализации базы данных:**
    


5. **Запустите сервер:**

   ```bash
    python .back/app.py
   ```
   
6. **Запустите клиентское приложение**
   ```python
   python .client/main.py 
   ```
