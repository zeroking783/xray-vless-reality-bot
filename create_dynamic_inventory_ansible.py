#!/usr/bin/env python3

from logger import logger
import psycopg2
import csv
import json
from dotenv import load_dotenv
import os
from vault_func import get_vault_token, create_vault_client, read_secret_vault
from db_func import connect_to_db

vault_token = get_vault_token()

client = create_vault_client("https://127.0.0.1:8200", vault_token, "/etc/ssl/certs/vault-cert.pem")

data_db_connect = read_secret_vault(client, 'Cloak/databases/settings_server_db')

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
    SELECT * FROM servers.initial WHERE ready = False;
"""


conn, cursor = connect_to_db(data_db_connect["db_host"], 
                            data_db_connect["db_port"], 
                            data_db_connect["db_name"], 
                            data_db_connect["db_user"], 
                            data_db_connect["user_password"])


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

        base_dynamic_inventory["_meta"]["hostvars"][inventory_hostname] = server_data
        base_dynamic_inventory["xray-workers"]["hosts"].append(inventory_hostname)
        logger.info(f"Новый сервер {inventory_hostname} с ip {server_data["ansible_host"]} "
                    f"успешно добавлен в dynamic inventory")
    except Exception as e:
        logger.error(f"Не удалось добавить новый сервер {inventory_hostname} \n{server_data} в dynamic_inventory")

base_dynamic_inventory_json = json.dumps(base_dynamic_inventory, indent=4)
logger.info(f"Динамическое инвентарное хранилище: \n{base_dynamic_inventory_json}")
print(base_dynamic_inventory_json)


logger.debug(f"Закрываю соединение с базой данных {data_db_connect["db_name"]}")
try:
    cursor.close()
    conn.close()
    logger.info(f"Соединение с базой данных {data_db_connect["db_name"]} закрыто")
except Exception as e:
    logger.error(f"Не удалось закрыть соединение с базой данных")