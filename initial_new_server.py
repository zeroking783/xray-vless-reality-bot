from logger import logger
import psycopg2
import csv
import json
from dotenv import load_dotenv
import os

load_dotenv()

db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

query_insert_new_server = """
    INSERT INTO servers.initial (json_data) VALUES (%s);
"""

query_check_ansible_host = """
    SELECT id FROM servers.initial
    WHERE json_data ->> 'ansible_host' = %s;
"""

query_update_old_server = """
    UPDATE servers.initial
    SET json_data = %s, processed = False
    WHERE json_data ->> 'ansible_host' = %s;
"""

logger.info("Пытаюсь подключиться к базе данных")
try:
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password
    )
    cursor = conn.cursor()
    logger.info(f"Успешное подключение к базе данных")
except Exception as e:
    logger.error(f"Не удалось подключиться к базе данных: {e}")


logger.info("Открываю .csv файл с данными серверов")
with open("initial_new_servers_list.csv", newline='') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=';')
    for ip, password in csvreader:

        server_data = {
            "ansible_host": ip,
            "ansible_user": "root",
            "ansible_password": password
        }
        logger.info(f"Создаю объект json для сервера {ip}")
        try:
            server_data_json = json.dumps(server_data)
            logger.info(f"JSON сервера {ip} успешно создан")
        except Exception as e:
            logger.error(f"Ошибка при создании json для сервера {ip}: \n{e}")

        cursor.execute(query_check_ansible_host, (ip,))
        result = cursor.fetchone()

        if result:
            logger.info(f"Обновляю запись сервера {ip} в servers.initial")
            try:
                cursor.execute(query_update_old_server, (server_data_json, ip))
                logger.info(f"Обновление записи о сервере {ip} в servers.initial прошло успешно")
            except Exception as e:
                logger.error(f"Ошибка при обновлении записи о сервере {ip} servers.initial: \n{e}")
        else:
            logger.info(f"Добавляю новый сервер {ip} в servers.initial")
            try:
                cursor.execute(query_insert_new_server, (server_data_json, ))
                logger.info(f"Сервер {ip} успешно добавлен в servers.initial")
            except Exception as e:
                logger.error(f"Ошибка при добавлении сервера {ip} в servers.initial: \n{e}")

    conn.commit()

cursor.close()
conn.close()





