#!/usr/bin/env python3

from logger import logger
import psycopg2
import csv
import json
from dotenv import load_dotenv
import os

logger.debug(f"Считываю переменные окружения из файла")
try:
    load_dotenv()
    db_host = os.getenv("DB_INIT_HOST")
    db_port = os.getenv("DB_INIT_PORT")
    db_name = os.getenv("DB_INIT_NAME")
    db_user = os.getenv("DB_INIT_USER")
    db_password = os.getenv("DB_INIT_PASSWORD")
    logger.info(f"Переменные окружения из файла успешно считаны")
except Exception as e:
    logger.error(f"Не удалось считать переменные окружения из файла: \n{e}")


base_dynamic_inventory = {
    "_meta": {
        "hostvars": {}
    },
    "all": {
        "children": ["xray-workers"]
    },
    "xray-workers": {
        "hosts": []
    }
}


query_get_new_servers = """
    SELECT * FROM servers.initial WHERE processed = False;
"""


logger.debug(f"Пытаюсь подключиться к базе данных {db_name}")
try:
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password
    )
    cursor = conn.cursor()
    logger.info(f"Успешное подключение к базе данных {db_name}")
except Exception as e:
    logger.error(f"Не удалось подключиться к базе данных {db_name}: {e}")

logger.debug(f"Получаю новые сервера из servers.initial")
try:
    cursor.execute(query_get_new_servers)
    rows = cursor.fetchall()
    logger.info(f"Новые сервера из servers.initial успешно получены")
except Exception as e:
    logger.error(f"Ошибка при получении списка новых серверов из servers.initial: \n{e}")


for row in rows:
    id_server = row[0]
    inventory_hostname = "server-" + str(id_server)

    logger.debug(f"Добавляю в dynamic inventory новый сервер {inventory_hostname} "
                f"c ip {row[1]["ansible_host"]} из servers.initial")
    try:
        server_data = row[1]
        server_data["id"] = row[0]
        server_data["ansible_port"] = 22
        base_dynamic_inventory["_meta"]["hostvars"][inventory_hostname] = server_data
        base_dynamic_inventory["xray-workers"]["hosts"].append(inventory_hostname)
        logger.info(f"Новый сервер {inventory_hostname} с ip {server_data["ansible_host"]} "
                    f"успешно добавлен в dynamic inventory")
    except Exception as e:
        logger.error(f"Не удалось добавить новый сервер {inventory_hostname} \n{server_data} в dynamic_inventory")

base_dynamic_inventory_json = json.dumps(base_dynamic_inventory, indent=4)
logger.info(f"Динамическое инвентарное хранилище: \n{base_dynamic_inventory_json}")
print(base_dynamic_inventory_json)


logger.debug(f"Закрываю соединение с базой данных {db_name}")
try:
    cursor.close()
    conn.close()
    logger.info(f"Соединение с базой данных {db_name} закрыто")
except Exception as e:
    logger.error(f"Не удалось закрыть соединение с базой данных")