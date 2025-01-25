from logger import logger
import psycopg2
import csv
import json
from dotenv import load_dotenv
import os
import hvac
from vault_func import get_vault_token, create_vault_client, read_secret_vault
from db_func import connect_to_db
        


vault_token = get_vault_token()

client = create_vault_client("https://127.0.0.1:8200", vault_token, "/etc/ssl/certs/vault-cert.pem")

data_db_connect = read_secret_vault(client, 'Cloak/databases/settings_server_db')

query_insert_new_server = """
    INSERT INTO servers.initial (connect_data) VALUES (%s);
"""

query_check_ansible_host = """
    SELECT id FROM servers.initial
    WHERE connect_data ->> 'ansible_host' = %s;
"""

query_update_old_server = """
    UPDATE servers.initial
    SET connect_data = %s, ready = False
    WHERE connect_data ->> 'ansible_host' = %s;
"""

conn, cursor = connect_to_db(data_db_connect["db_host"], 
                            data_db_connect["db_port"], 
                            data_db_connect["db_name"], 
                            data_db_connect["db_user"], 
                            data_db_connect["user_password"])


logger.debug("Открываю .csv файл с данными серверов")
with open("add_new_servers_list.csv", newline='') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=';')
    for ip, port, password in csvreader:

        server_data = {
            "ansible_host": ip,
            "ansible_port": port,
            "ansible_user": "root",
            "ansible_password": password
        }
        logger.debug(f"Создаю объект json для сервера {ip}")
        try:
            server_data_json = json.dumps(server_data)
            logger.info(f"JSON сервера {ip} успешно создан")
        except Exception as e:
            logger.error(f"Ошибка при создании json для сервера {ip}: \n{e}")

        cursor.execute(query_check_ansible_host, (ip,))
        result = cursor.fetchone()

        if result:
            logger.debug(f"Обновляю запись сервера {ip} в servers.initial")
            try:
                cursor.execute(query_update_old_server, (server_data_json, ip))
                logger.info(f"Обновление записи о сервере {ip} в servers.initial прошло успешно")
            except Exception as e:
                logger.error(f"Ошибка при обновлении записи о сервере {ip} servers.initial: \n{e}")
        else:
            logger.debug(f"Добавляю новый сервер {ip} в servers.initial")
            try:
                cursor.execute(query_insert_new_server, (server_data_json, ))
                logger.info(f"Сервер {ip} успешно добавлен в servers.initial")
            except Exception as e:
                logger.error(f"Ошибка при добавлении сервера {ip} в servers.initial: \n{e}")

    conn.commit()

cursor.close()
conn.close()





