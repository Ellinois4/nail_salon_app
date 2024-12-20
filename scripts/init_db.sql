

-- Таблица ролей
CREATE TABLE roles
(
    role_id     serial PRIMARY KEY,
    role_name   varchar(50) NOT NULL UNIQUE,
    permissions varchar(255)
);

ALTER TABLE roles OWNER TO admin;

-- Таблица пользователей
CREATE TABLE users
(
    user_id       serial PRIMARY KEY,
    username      varchar(50) NOT NULL UNIQUE,
    password_hash varchar(255) NOT NULL,
    role_id       integer REFERENCES roles(role_id)
);

ALTER TABLE users OWNER TO admin;

-- Таблица клиентов
CREATE TABLE clients
(
    client_id   serial PRIMARY KEY,
    client_name varchar(100) NOT NULL,
    phone       varchar(15) UNIQUE NOT NULL,
    birth_date  date
);

ALTER TABLE clients OWNER TO admin;

-- Таблица мастеров
CREATE TABLE masters
(
    master_id   serial PRIMARY KEY,
    master_name varchar(100) NOT NULL,
    phone       varchar(15) UNIQUE
);

ALTER TABLE masters OWNER TO admin;

-- Таблица услуг
CREATE TABLE services
(
    service_id   serial PRIMARY KEY,
    service_name varchar(255) NOT NULL,
    description  text,
    price        numeric(10, 2) NOT NULL,
    duration     integer NOT NULL, -- Время в минутах
);

ALTER TABLE services OWNER TO admin;

-- Таблица записей на прием (appointments)
CREATE TABLE appointments
(
    appointment_id serial PRIMARY KEY,
    client_id      integer REFERENCES clients(client_id),
    master_id      integer REFERENCES masters(master_id),
    service_id     integer REFERENCES services(service_id),
    appointment_date timestamp NOT NULL,
    status         varchar(50) DEFAULT 'Запланировано'
);

ALTER TABLE appointments OWNER TO admin;

-- Таблица платежей (payments)
CREATE TABLE payments
(
    payment_id     serial PRIMARY KEY,
    client_id      integer REFERENCES clients(client_id),
    payment_amount numeric(10, 2) NOT NULL,
    payment_date   timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payment_method varchar(50) -- Например, наличные, карта и т.д.
);

ALTER TABLE payments OWNER TO admin;

-- Вставка начальных данных в таблицы

-- Вставка данных о ролях
INSERT INTO roles (role_name, permissions) VALUES
('Администратор', 'Все права'),
('Мастер', 'Редактирование услуг и записи'),
('Пользователь', 'Запись на прием');

-- Вставка пользователей
INSERT INTO users (username, password_hash, role_id) VALUES
('admin', 'hashedpassword123', 1),
('master1', 'hashedpassword456', 2),
('client1', 'hashedpassword789', 3),
('client2', 'hashedpassword101', 3),
('master2', 'hashedpassword202', 2);

-- Вставка клиентов
INSERT INTO clients (client_name, phone, birth_date) VALUES
('Анна Иванова', '+380501234567', '1990-05-15'),
('Мария Смирнова', '+380671234567', '1985-03-22'),
('Ирина Сидорова', '+380631234567', '2000-07-10'),
('Ольга Петрова', '+380631234888', '1992-08-01'),
('Екатерина Васильева', '+380981234567', '1995-01-15');

-- Вставка мастеров
INSERT INTO masters (master_name, phone) VALUES
('Александра Михайлова', '+380501234567'),
('Ирина Коваленко', '+380671234888'),
('Наталья Попова', '+380681234567'),
('Елена Василенко', '+380951234567'),
('Виктория Шевченко', '+380971234567');

-- Вставка услуг
INSERT INTO services (service_name, description, price, duration) VALUES
('Маникюр', 'Классический маникюр с покрытием', 300.00, 60),
('Педикюр', 'Классический педикюр с покрытием', 350.00, 75),
('Парафинотерапия', 'Парафинотерапия для рук или ног', 150.00, 30),
('Массаж рук', 'Массаж рук с увлажняющим кремом', 100.00, 20),
('Дизайн ногтей', 'Модный дизайн ногтей', 200.00, 45),
('Шеллак маникюр', 'Маникюр с покрытием шеллак', 350.00, 60),
('Ремонт ногтей', 'Ремонт поврежденных ногтей', 100.00, 30),
('Френч маникюр', 'Классический французский маникюр', 400.00, 60),
('Укрепление ногтей', 'Укрепление ногтей гелем или акрилом', 250.00, 45),
('Педикюр с массажем', 'Педикюр с расслабляющим массажем ног', 400.00, 90);

-- Вставка записей на прием
INSERT INTO appointments (client_id, master_id, service_id, appointment_date, status) VALUES
(1, 1, 1, '2024-12-15 10:00:00', 'Запланировано'),
(2, 2, 3, '2024-12-16 14:00:00', 'Запланировано'),
(3, 3, 2, '2024-12-17 16:30:00', 'Запланировано'),
(4, 4, 4, '2024-12-18 11:00:00', 'Запланировано'),
(5, 5, 5, '2024-12-19 13:30:00', 'Запланировано'),
(1, 2, 6, '2024-12-20 09:00:00', 'Запланировано'),
(2, 1, 7, '2024-12-21 15:00:00', 'Запланировано');

-- Вставка платежей
INSERT INTO payments (client_id, payment_amount, payment_date, payment_method) VALUES
(1, 500.00, '2024-12-15 10:00:00', 'Карта'),
(2, 700.00, '2024-12-16 14:00:00', 'Наличные'),
(3, 300.00, '2024-12-17 16:30:00', 'Карта'),
(4, 400.00, '2024-12-18 11:00:00', 'Наличные'),
(5, 500.00, '2024-12-19 13:30:00', 'Карта');
