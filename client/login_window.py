import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox


class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success  # Сохраняем обработчик успешного входа
        self.setWindowTitle("Авторизация")  # Устанавливаем заголовок окна
        self.setGeometry(100, 100, 300, 200)  # Устанавливаем размеры окна

        # Применение стиля
        self.setStyleSheet("""
            QWidget {
                background-color: #f7f7f7;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QLabel {
                color: #333;
                font-weight: bold;
                margin-bottom: 4px;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d7;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
            QPushButton:pressed {
                background-color: #004f91;
            }
        """)

        # Создаем интерфейс
        layout = QVBoxLayout()

        self.username_label = QLabel("Логин:")
        self.username_label.setAlignment(Qt.AlignLeft)
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Введите ваш логин")

        self.password_label = QLabel("Пароль:")
        self.password_label.setAlignment(Qt.AlignLeft)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Введите ваш пароль")

        self.login_button = QPushButton("Войти", self)
        self.login_button.clicked.connect(self.login)  

        # Добавляем элементы в макет
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def login(self):
        """Обработчик логина."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.show_error("Пожалуйста, заполните все поля.")
            return

        try:
            response = requests.post('http://localhost:5000/auth/login', json={
                'username': username,
                'password': password
            })

            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                if token:
                    self.on_login_success(token)  # Вызываем переданный обработчик
                    self.close()  # Закрываем окно авторизации
                else:
                    self.show_error("Токен доступа отсутствует в ответе сервера.")
            else:
                message = response.json().get('message', 'Ошибка авторизации')
                self.show_error(message)
        except requests.exceptions.RequestException as e:
            self.show_error(f"Ошибка соединения: {e}")

    def show_error(self, message):
        """Показать сообщение об ошибке."""
        QMessageBox.critical(self, "Ошибка", message)
