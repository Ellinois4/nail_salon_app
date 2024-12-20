import csv
import json
import threading

import jwt 
import requests
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QMessageBox, QDateEdit, QDialog
)


class Worker(QObject):
    """Класс для выполнения сетевых запросов в отдельном потоке."""
    appointments_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, token):
        super().__init__()
        self.token = token

    def fetch_appointments(self):
        """Получение списка записей на услуги."""
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            response = requests.get('http://localhost:5000/appointment', headers=headers)
            if response.status_code == 200:
                appointments = response.json()
                self.appointments_updated.emit(appointments)
            else:
                message = response.json().get('message', 'Ошибка получения данных')
                self.error_occurred.emit(message)
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("Не удалось подключиться к серверу")
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Ошибка запроса: {e}")


class NailSalonApp(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.setWindowTitle("Управление маникюрным салоном")
        self.setGeometry(100, 100, 1200, 600)

        self.user_role_id = self.get_user_role()

        self.setStyleSheet("""
            QWidget { background-color: #f7f7f7; font-family: Arial, sans-serif; font-size: 14px; }
            QPushButton { background-color: #0078d7; color: white; border: none; border-radius: 6px; padding: 8px 16px; }
            QPushButton:hover { background-color: #005bb5; }
            QTableWidget { border: 1px solid #ddd; gridline-color: #ddd; background-color: white; font-size: 13px; }
            QHeaderView::section { background-color: #e7e7e7; color: #333; font-weight: bold; border: 1px solid #ccc; }
        """)

        # Таблица записи на услуги
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Клиент", "Мастер", "Услуга", "Дата", "Статус", "Сумма", "Статус оплаты"
        ])
        self.table.setAlternatingRowColors(True)

        # Основной макет
        layout = QVBoxLayout()
        layout.addWidget(self.table)

        # Панель с кнопками
        button_layout = QHBoxLayout()

        self.button_refresh = QPushButton("Обновить")
        self.button_refresh.clicked.connect(self.refresh_appointments)
        button_layout.addWidget(self.button_refresh)

        if self.user_role_id in [1, 2]:  # Администратор или Работник
            self.button_create = QPushButton("Создать запись")
            self.button_create.clicked.connect(self.create_appointment_window)
            button_layout.addWidget(self.button_create)

            self.button_export = QPushButton("Экспорт в CSV")
            self.button_export.clicked.connect(self.export_appointments_csv)
            button_layout.addWidget(self.button_export)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Настройка рабочего потока
        self.worker = Worker(self.token)
        self.worker.appointments_updated.connect(self.update_table)
        self.worker.error_occurred.connect(self.show_error)

        # Загрузка начальных данных
        self.refresh_appointments()

    def get_user_role(self):
        try:
            decoded = jwt.decode(self.token, options={"verify_signature": False})
            identity = json.loads(decoded.get('sub', '{}'))
            role_id = identity.get('role_id')
            if role_id is None:
                raise ValueError("Token does not contain role_id")
            return int(role_id)
        except jwt.ExpiredSignatureError:
            self.show_error("Срок действия токена истек.")
            return None
        except jwt.InvalidTokenError as e:
            self.show_error(f"Неверный токен: {e}")
            return None
        except Exception as e:
            self.show_error(f"Ошибка определения роли пользователя: {e}")
            return None

    def show_error(self, message):
        """Показать ошибку пользователю"""
        QMessageBox.critical(self, "Ошибка", message)

    def refresh_appointments(self):
        """Обновить список записей на услуги"""
        threading.Thread(target=self.worker.fetch_appointments, daemon=True).start()

    def update_table(self, appointments):
        """Обновляет таблицу с записями"""
        self.table.setRowCount(0)
        for item in appointments:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('appointment_id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(item.get('client_name', '')))
            self.table.setItem(row, 2, QTableWidgetItem(item.get('master_name', '')))
            self.table.setItem(row, 3, QTableWidgetItem(item.get('service_name', '')))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('appointment_date', ''))))
            self.table.setItem(row, 5, QTableWidgetItem(item.get('appointment_status', '')))
            self.table.setItem(row, 6, QTableWidgetItem(str(item.get('amount', ''))))
            self.table.setItem(row, 7, QTableWidgetItem(item.get('payment_status', '')))

    def create_appointment_window(self):
        """Окно для создания записи на услугу"""
        self.appointment_window = QDialog(self)
        self.appointment_window.setWindowTitle("Создать запись")
        self.appointment_window.setModal(True)
        layout = QVBoxLayout()

        fields = {
            "Клиент": QComboBox(),
            "Мастер": QComboBox(),
            "Услуга": QComboBox(),
            "Дата и время": QDateEdit(calendarPopup=True)
        }

        for label, widget in fields.items():
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        self.load_clients(fields["Клиент"])
        self.load_masters(fields["Мастер"])
        self.load_services(fields["Услуга"])

        # Кнопка для создания записи
        def create_appointment():
            client_id = fields["Клиент"].currentData()
            master_id = fields["Мастер"].currentData()
            service_id = fields["Услуга"].currentData()
            appointment_date = fields["Дата и время"].date().toString('yyyy-MM-dd')

            if not all([client_id, master_id, service_id, appointment_date]):
                QMessageBox.warning(self.appointment_window, "Предупреждение", "Пожалуйста, заполните все поля.")
                return

            data = {
                'client_id': client_id,
                'master_id': master_id,
                'service_id': service_id,
                'appointment_date': appointment_date
            }
            headers = {'Authorization': f'Bearer {self.token}'}

            try:
                response = requests.post('http://localhost:5000/appointment', json=data, headers=headers)
                if response.status_code == 201:
                    QMessageBox.information(self.appointment_window, "Успех", "Запись на услугу успешно создана.")
                    self.refresh_appointments()
                    self.appointment_window.close()
                else:
                    message = response.json().get('message', 'Ошибка создания записи')
                    self.show_error(message)
            except requests.exceptions.RequestException as e:
                self.show_error(f"Ошибка запроса: {e}")

        button_create = QPushButton("Создать запись")
        button_create.clicked.connect(create_appointment)
        layout.addWidget(button_create)

        self.appointment_window.setLayout(layout)
        self.appointment_window.show()

    def export_appointments_csv(self):
        """Экспорт данных о записях на услуги в CSV файл"""
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            # Отправляем GET-запрос на сервер для получения данных о записях
            response = requests.get('http://localhost:5000/appointment', headers=headers)
            if response.status_code == 200:
                appointments = response.json()

                # Создаем и открываем файл для записи
                with open("appointments.csv", "w", newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)

                    # Записываем заголовки
                    writer.writerow([
                        "ID", "Клиент", "Мастер", "Услуга", "Дата", "Статус", "Сумма", "Статус оплаты"
                    ])

                    # Записываем данные
                    for item in appointments:
                        writer.writerow([
                            item.get('appointment_id', ''),
                            item.get('client_name', ''),
                            item.get('master_name', ''),
                            item.get('service_name', ''),
                            item.get('appointment_date', ''),
                            item.get('appointment_status', ''),
                            item.get('amount', ''),
                            item.get('payment_status', '')
                        ])

                # Сообщение об успешном экспорте
                QMessageBox.information(self, "Успех", "Данные экспортированы в appointments.csv")
            else:
                message = response.json().get('message', 'Ошибка экспорта данных')
                self.show_error(message)

        except requests.exceptions.RequestException as e:
            self.show_error(f"Ошибка запроса: {e}")

    def load_clients(self, combo_box):
        """Загрузка списка клиентов в ComboBox"""
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            response = requests.get('http://localhost:5000/clients', headers=headers)
            if response.status_code == 200:
                clients = response.json()
                for client in clients:
                    display_text = f"{client.get('name', '')} - {client.get('phone', '')}"
                    combo_box.addItem(display_text, client.get('client_id'))
            else:
                self.show_error(response.json().get('message', 'Ошибка загрузки клиентов'))
        except requests.exceptions.RequestException as e:
            self.show_error(f"Ошибка запроса: {e}")

    def load_masters(self, combo_box):
        """Загрузка списка мастеров в ComboBox"""
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            response = requests.get('http://localhost:5000/masters', headers=headers)
            if response.status_code == 200:
                masters = response.json()
                for master in masters:
                    display_text = f"{master.get('name', '')} - {master.get('specialty', '')}"
                    combo_box.addItem(display_text, master.get('master_id'))
            else:
                self.show_error(response.json().get('message', 'Ошибка загрузки мастеров'))
        except requests.exceptions.RequestException as e:
            self.show_error(f"Ошибка запроса: {e}")

    def load_services(self, combo_box):
        """Загрузка списка услуг в ComboBox"""
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            response = requests.get('http://localhost:5000/services', headers=headers)
            if response.status_code == 200:
                services = response.json()
                for service in services:
                    display_text = f"{service.get('name', '')} - {service.get('price', '')} руб."
                    combo_box.addItem(display_text, service.get('service_id'))
            else:
                self.show_error(response.json().get('message', 'Ошибка загрузки услуг'))
        except requests.exceptions.RequestException as e:
            self.show_error(f"Ошибка запроса: {e}")

    def load_masters(self, combo_box):
        """Загрузка списка мастеров в ComboBox"""
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get('http://localhost:5000/clients', headers=headers)
        if response.status_code == 200:
            masters = response.json()
            for master in masters:
                combo_box.addItem(f"{master['name']} - {master['phone']}", master['client_id'])
