from flask_sqlalchemy import SQLAlchemy

from db import db

class Role(db.Model):
    __tablename__ = 'roles'

    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.Column(db.String(255))

    def __repr__(self):
        return f"<Role(role_id={self.role_id}, role_name={self.role_name})>"

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'))

    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>"

class Client(db.Model):
    __tablename__ = 'clients'

    client_id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    birth_date = db.Column(db.Date)

    def __repr__(self):
        return f"<Client(id={self.id}, client_name={self.client_name})>"

class Service(db.Model):
    __tablename__ = 'services'

    service_id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Продолжительность в минутах

    def __repr__(self):
        return f"<Service(id={self.id}, name={self.name}, price={self.price})>"

class Master(db.Model):
    __tablename__ = 'masters'

    master_id = db.Column(db.Integer, primary_key=True)
    master_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True)

    def __repr__(self):
        return f"<Master(id={self.id}, master_name={self.master_name})>"

class Appointment(db.Model):
    __tablename__ = 'appointments'

    appointment_id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    master_id = db.Column(db.Integer, db.ForeignKey('masters.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_status = db.Column(db.String(50), default='Запланировано') 

    client = db.relationship('Client', backref=db.backref('appointments', lazy=True))
    master = db.relationship('Master', backref=db.backref('appointments', lazy=True))
    service = db.relationship('Service', backref=db.backref('appointments', lazy=True))

    def __repr__(self):
        return f"<Appointment(id={self.id}, client_id={self.client_id}, master_id={self.master_id}, service_id={self.service_id})>"

class Payment(db.Model):
    __tablename__ = 'payments'

    payment_id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(50), default='Завершено')

    client = db.relationship('Client', backref=db.backref('payments', lazy=True))
    appointment = db.relationship('Appointment', backref=db.backref('payments', lazy=True))

    def __repr__(self):
        return f"<Payment(payment_id={self.payment_id}, client_id={self.client_id}, amount={self.amount}, payment_method={self.payment_method})>"
