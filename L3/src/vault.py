from logger import logger
import os
import hvac

def get_vault_token():
    logger.info(f"Читаю VAULT_TOKEN из переменных окружения")
    vault_token = os.getenv('VAULT_TOKEN')
    if not vault_token:
        logger.error(f"VAULT_TOKEN не установлен в переменных окружения")
        sys.exit("VAULT_TOKEN не установлен в переменных окружения")
    logger.debug(f"VAULT_TOKEN успешно прочитан")
    return vault_token


def create_vault_client(vault_url, token, cert_path):
    logger.info(f"Прохожу аунтефикацию на Vault")
    try:
        client = hvac.Client(url=vault_url, token=token, verify=cert_path)
        if client.is_authenticated():
            logger.debug(f"Успешная аунтификация в Vault")
            return client
    except Exception as e:
        logger.error(f"Не удалось пройти аунтификацию в Vault:\n{e}")
        sys.exit(f"Не удалось пройти аунтификацию в Vault:\n{e}")


def read_secret_vault(client, path, only_data=True):
    logger.info(f"Начинаю читать данные в Vault")
    try:
        response = client.secrets.kv.read_secret_version(path=path)
        logger.debug(f"Запрос в Vault выполнен успешно")
        if "data" in response and "data" in response["data"]:
            logger.debug(f"Данные сущесвтуют и успешно прочитаны")
            if only_data:
                return response["data"]["data"]
            else:
                return response
    except Exception as e:
        logger.eror(f"Ошибка при чтении данных в Vault:\n{e}")
        sys.exit(f"Ошибка при чтении данных в Vault")