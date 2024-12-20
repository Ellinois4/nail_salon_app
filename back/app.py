import os
import subprocess
from datetime import datetime
import sys

from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required
from sqlalchemy import text

from back.auth import auth_bp
from back.db import db, migrate
from back.utils import role_required

import jwt  

jwt_manager = JWTManager()  

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:2971@localhost/nail_salon'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'your_secret_key'

    db.init_app(app)
    migrate.init_app(app, db)
    jwt_manager.init_app(app)

    with app.app_context():
        # Создаем все таблицы
        db.create_all()

        # Создаем роли по умолчанию, если их нет
        default_roles = [
            {'role_id': 1, 'role_name': 'Администратор', 'permissions': 'all'},
            {'role_id': 2, 'role_name': 'Работник', 'permissions': 'edit'},
            {'role_id': 3, 'role_name': 'Пользователь', 'permissions': 'view'}
        ]

        for role_data in default_roles:
            existing_role = db.session.execute(
                text("SELECT * FROM roles WHERE role_id = :role_id"), {'role_id': role_data['role_id']}
            ).fetchall()

            if not existing_role:
                db.session.execute(
                    text(
                        "INSERT INTO roles (role_id, role_name, permissions) VALUES (:role_id, :role_name, :permissions)"),
                    role_data
                )

        db.session.commit()


    app.register_blueprint(auth_bp, url_prefix='/auth')

    @app.route('/clients', methods=['GET'])
    @jwt_required()
    @role_required([1, 2])  
    def get_clients():
        try:
            clients = db.session.execute(
                text("SELECT client_id, client_name, phone, birth_date FROM clients")
            ).fetchall()

            client_list = []
            for client in clients:
                client_list.append({
                    'client_id': client.client_id,
                    'name': client.client_name,
                    'phone': client.phone,
                    'birth_date': client.birth_date
                })

            return jsonify(client_list), 200
        except Exception as e:
            print(f"Error in /clients: {e}")
            return jsonify({"message": "Ошибка на сервере"}), 500

    @app.route('/services', methods=['GET'])
    @jwt_required()
    def get_services():
        try:
            services = db.session.execute(
                text("SELECT service_id, service_name, description, price, duration FROM services")
            ).fetchall()

            service_list = []
            for service in services:
                service_list.append({
                    'service_id': service.service_id,
                    'name': service.service_name,
                    'description': service.description,
                    'price': service.price,
                    'duration': service.duration
                })

            return jsonify(service_list), 200

        except Exception as e:
            print(f"Error in /services: {e}")
            return jsonify({"message": f"Ошибка при получении услуг: {str(e)}"}), 500

    @app.route('/appointment', methods=['GET'])
    @jwt_required()
    def get_appointment():
        try:
            appointment_items = db.session.execute(
                text("""SELECT 
                                a.appointment_id, 
                                c.client_name, 
                                m.master_name, 
                                s.service_name, 
                                a.appointment_date, 
                                a.status, 
                                p.payment_amount
                            FROM appointments a
                            LEFT JOIN payments p ON a.appointment_id = p.appointment_id
                            LEFT JOIN clients c ON a.client_id = c.client_id
                            LEFT JOIN masters m ON a.master_id = m.master_id
                            LEFT JOIN services s ON a.service_id = s.service_id""")
            ).mappings().fetchall()

            result = []

            for item in appointment_items:
                result.append({
                    'appointment_id': item['appointment_id'], 
                    'client_name': item['client_name'],
                    'master_name': item['master_name'],
                    'payment_amount': float(item['payment_amount']) if item['payment_amount'] else 0.0, 
                    'service_name': item['service_name'],
                    'appointment_date': item['appointment_date'],
                    'status': item['status']
                })

            return jsonify(result), 200
        except Exception as e:
            print(f"Error on server: {e}")
            return jsonify({"message": "Server error"}), 500

    @app.route('/appointment', methods=['POST'])
    @jwt_required()
    @role_required([1, 2])
    def create_appointment():
        try:
            data = request.get_json()
            client_id = data['client_id']
            master_id = data['master_id']
            service_id = data['service_id']
            appointment_date = data['appointment_date']

            # Проверка наличия клиента
            client = db.session.execute(
                text("SELECT * FROM clients WHERE client_id = :client_id"),
                {'client_id': client_id}
            ).fetchone()

            if not client:
                return jsonify({"message": "Клиент не найден"}), 404

            # Проверка наличия мастера
            master = db.session.execute(
                text("SELECT * FROM masters WHERE master_id = :master_id"),
                {'master_id': master_id}
            ).fetchone()

            if not master:
                return jsonify({"message": "Мастер не найден"}), 404

            # Проверка наличия услуги
            service = db.session.execute(
                text("SELECT * FROM services WHERE service_id = :service_id"),
                {'service_id': service_id}
            ).fetchone()

            if not service:
                return jsonify({"message": "Услуга не найдена"}), 404

            # Проверка доступности мастера на указанную дату
            existing_appointments = db.session.execute(
                text("""
                    SELECT * FROM appointments 
                    WHERE master_id = :master_id 
                    AND appointment_date = :appointment_date
                """),
                {'master_id': master_id, 'appointment_date': appointment_date}
            ).fetchall()

            if existing_appointments:
                return jsonify({"message": "Мастер занят в это время"}), 400

            # Создание новой записи о записи на услугу
            db.session.execute(
                text("""
                    INSERT INTO appointments (client_id, master_id, service_id, appointment_date)
                    VALUES (:client_id, :master_id, :service_id, :appointment_date)
                """),
                {
                    'client_id': client_id,
                    'master_id': master_id,
                    'service_id': service_id,
                    'appointment_date': appointment_date
                }
            )

            db.session.commit()

            return jsonify({"message": "Запись на услугу успешно создана"}), 201
        except Exception as e:
            db.session.rollback()  
            print(f"Error in /appointment POST: {e}")
            return jsonify({"message": "Ошибка на сервере"}), 500

    @app.route('/payment', methods=['POST'])
    @jwt_required()
    @role_required([1, 2])
    def process_payment():
        try:
            data = request.get_json()
            client_id = data['client_id']
            appointment_id = data['appointment_id']
            payment_amount = data['payment_amount']
            payment_method = data['payment_method']

            # Получение текущего времени для поля payment_date
            payment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Проверка существования записи
            appointment = db.session.execute(
                text("SELECT * FROM appointments WHERE appointment_id = :appointment_id"),
                {'appointment_id': appointment_id}
            ).fetchone()

            if not appointment:
                return jsonify({"message": "Запись не найдена"}), 404

            # Создание записи об оплате
            db.session.execute(
                text("""
                    INSERT INTO payments (client_id, appointment_id, payment_amount, payment_method, payment_date)
                    VALUES (:client_id, :appointment_id, :payment_amount, :payment_method, :payment_date)
                """),
                {
                    'client_id': client_id,
                    'appointment_id': appointment_id,
                    'payment_amount': payment_amount,
                    'payment_method': payment_method,
                    'payment_date': payment_date
                }
            )

            # Обновление статуса записи на "Завершено"
            db.session.execute(
                text("""
                    UPDATE appointments
                    SET status = 'Завершено'
                    WHERE appointment_id = :appointment_id
                """),
                {'appointment_id': appointment_id}
            )

            db.session.commit()

            return jsonify({"message": "Оплата успешно проведена"}), 200

        except Exception as e:
            db.session.rollback()  
            print(f"Error in /payment POST: {e}")
            return jsonify({"message": "Ошибка на сервере"}), 500

    @app.route('/service', methods=['POST'])
    @jwt_required()
    @role_required([1, 2])
    def add_service():
        try:
            data = request.get_json()
            service_name = data['service_name']
            description = data.get('description', '')
            price = data['price']
            duration = data['duration']

            # Проверка, существует ли услуга с таким названием
            existing_service = db.session.execute(
                text("SELECT * FROM services WHERE service_name = :service_name"),
                {'service_name': service_name}
            ).fetchone()

            if existing_service:
                return jsonify({"message": "Услуга с таким названием уже существует"}), 400

            # Добавление новой услуги
            db.session.execute(
                text("""
                    INSERT INTO services (service_name, description, price, duration)
                    VALUES (:service_name, :description, :price, :duration)
                """),
                {
                    'service_name': service_name,
                    'description': description,
                    'price': price,
                    'duration': duration
                }
            )
            db.session.commit()

            return jsonify({"message": "Услуга успешно добавлена"}), 201
        except Exception as e:
            db.session.rollback()  
            print(f"Error in /service POST: {e}")
            return jsonify({"message": "Ошибка на сервере"}), 500

    @app.route('/service/<int:service_id>', methods=['DELETE'])
    @jwt_required()
    @role_required([1, 2])
    def delete_service(service_id):
        try:
            # Проверка существования услуги
            service = db.session.execute(
                text("SELECT * FROM services WHERE service_id = :service_id"),
                {'service_id': service_id}
            ).fetchone()

            if not service:
                return jsonify({"message": "Услуга не найдена"}), 404

            # Удаление услуги
            db.session.execute(
                text("DELETE FROM services WHERE service_id = :service_id"),
                {'service_id': service_id}
            )
            db.session.commit()

            return jsonify({"message": "Услуга успешно удалена"}), 200
        except Exception as e:
            db.session.rollback() 
            print(f"Error in /service DELETE: {e}")
            return jsonify({"message": "Ошибка на сервере"}), 500

    @app.route('/master', methods=['POST'])
    @jwt_required()
    @role_required([1, 2])
    def add_master():
        try:
            data = request.get_json()
            master_name = data['master_name']
            phone = data['phone']
            email = data.get('email', '')  
            

            existing_master = db.session.execute(
                text("SELECT * FROM masters WHERE phone = :phone"),
                {'phone': phone}
            ).fetchone()

            if existing_master:
                return jsonify({"message": "Мастер с таким номером телефона уже существует"}), 400

            # Добавление нового мастера
            db.session.execute(
                text("""
                    INSERT INTO masters (master_name, phone, email)
                    VALUES (:master_name, :phone, :email)
                """),
                {
                    'master_name': master_name,
                    'phone': phone,
                    'email': email
                }
            )
            db.session.commit()

            return jsonify({"message": "Мастер успешно добавлен"}), 201
        except Exception as e:
            db.session.rollback()  
            print(f"Error in /master POST: {e}")
            return jsonify({"message": "Ошибка на сервере"}), 500

    @app.route('/master/<int:master_id>', methods=['DELETE'])
    @jwt_required()
    @role_required([1, 2])
    def delete_master(master_id):
        try:
            # Проверка существования мастера
            master = db.session.execute(
                text("SELECT * FROM masters WHERE master_id = :master_id"),
                {'master_id': master_id}
            ).fetchone()

            if not master:
                return jsonify({"message": "Мастер не найден"}), 404

            # Удаление мастера
            db.session.execute(
                text("DELETE FROM masters WHERE master_id = :master_id"),
                {'master_id': master_id}
            )
            db.session.commit()

            return jsonify({"message": "Мастер успешно удален"}), 200
        except Exception as e:
            db.session.rollback()  
            print(f"Error in /master DELETE: {e}")
            return jsonify({"message": "Ошибка на сервере"}), 500

    @app.route('/client', methods=['POST'])
    @jwt_required()
    @role_required([1, 2])
    def add_client():
        try:
            data = request.get_json()
            client_name = data['client_name']
            phone = data['phone']
            birth_date = data.get('birth_date')  

            # Проверка, существует ли клиент с таким номером телефона
            existing_client = db.session.execute(
                text("SELECT * FROM clients WHERE phone = :phone"),
                {'phone': phone}
            ).fetchone()

            if existing_client:
                return jsonify({"message": "Клиент с таким номером телефона уже существует"}), 400

            # Добавление нового клиента
            db.session.execute(
                text("""
                    INSERT INTO clients (client_name, phone, birth_date)
                    VALUES (:client_name, :phone, :birth_date)
                """),
                {
                    'client_name': client_name,
                    'phone': phone,
                    'birth_date': birth_date
                }
            )
            db.session.commit()

            return jsonify({"message": "Клиент успешно добавлен"}), 201
        except Exception as e:
            db.session.rollback()  
            print(f"Error in /client POST: {e}")
            return jsonify({"message": "Ошибка на сервере"}), 500

    @app.route('/client/<int:client_id>', methods=['DELETE'])
    @jwt_required()
    @role_required([1, 2])
    def delete_client(client_id):
        try:
            # Проверка существования клиента
            client = db.session.execute(
                text("SELECT * FROM clients WHERE client_id = :client_id"),
                {'client_id': client_id}
            ).fetchone()

            if not client:
                return jsonify({"message": "Клиент не найден"}), 404

            # Удаление клиента
            db.session.execute(
                text("DELETE FROM clients WHERE client_id = :client_id"),
                {'client_id': client_id}
            )
            db.session.commit()

            return jsonify({"message": "Клиент успешно удален"}), 200
        except Exception as e:
            db.session.rollback()  
            print(f"Error in /client DELETE: {e}")
            return jsonify({"message": "Ошибка на сервере"}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
