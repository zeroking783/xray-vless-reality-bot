import psycopg2
from vault_func import get_vault_token, create_vault_client, read_secret_vault
from logger import logger


def connect_to_db(host, port, dbname, user, password):
    logger.info(f"Пробую подключиться к базе данных {dbname}")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        logger.debug(f"Успешное подключение к базе данных {dbname}")
        return conn, cursor
    except Exception as e:
        logger.error(f"Не удалось подключиться к базе данных {dbname}: {e}")
        sys.exit(f"Не удалось подключиться к базе данных {dbname}: {e}")

