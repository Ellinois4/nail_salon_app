import sys
from PyQt5.QtWidgets import QApplication
from client.appointments_window import NailSalonApp
from client.login_window import LoginWindow


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.inventory_window = None  

        # Создаём окно авторизации
        self.login_window = LoginWindow(self.on_login_success)
        self.login_window.show()

    def on_login_success(self, token):
        """Обработчик успешного входа."""
        self.inventory_window = NailSalonApp(token)  
        self.inventory_window.show()
        self.login_window.close()  

    def run(self):
        sys.exit(self.app.exec())  


if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
