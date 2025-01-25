from logger import logger
from vault_func import get_vault_token, create_vault_client, read_secret_vault
import json
import psycopg2
from db_func import connect_to_db

vault_token = get_vault_token()
client = create_vault_client("https://127.0.0.1:8200", vault_token, "/etc/ssl/certs/vault-cert.pem")
data_db_connect = read_secret_vault(client, 'Cloak/databases/settings_server_db')


query_update_server_info = """
    UPDATE "servers"."initial"
    SET "connect_data" = %s,
        "ready" = true
    WHERE "id" = %s;
"""



try:
    logger.info(f"Читаю json файл с новыми данными о серверах")
    with open("test.json", "r") as file:
        servers_info = json.load(file)
        logger.debug(f"Json файл успешно прочитан")
except Exception as e:
    logger.error(f"Неизвестная ошибка при чтении файла:\n{e}")
    sys.exit(f"Неизвестная ошибка при чтении файла:\n{e}")


conn, cursor = connect_to_db(data_db_connect["db_host"], 
                            data_db_connect["db_port"], 
                            data_db_connect["db_name"], 
                            data_db_connect["db_user"], 
                            data_db_connect["user_password"])


for server, details in servers_info.items():
    id = int(details["current_hostname"].split("-")[-1])
    cursor.execute(query_update_server_info, (json.dumps(details), id))

conn.commit()
cursor.close()
conn.close()

    


print(servers_info)