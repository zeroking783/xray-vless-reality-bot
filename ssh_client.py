import logging
from logger import logger
import argparse
import paramiko
import time

def parse_arguments_for_ssh(default_ip=None, default_username="root", default_password=None, default_port=22, default_key_path=None):

    logger.info("Start parse arguments")
    parser = argparse.ArgumentParser(description="Example Python script to connect to a server")

    parser.add_argument('--ip', type=str, default=default_ip, help='IP address of the server')
    parser.add_argument('--username', type=str, default=default_username, help='The user for connect to via ssh')
    parser.add_argument('--password', type=str, default=default_password, help='Password for SSH login')
    parser.add_argument('--port', type=int, default=default_port, help="Port for SSH login")
    parser.add_argument('--key_path', type=str, default=default_key_path, help="Path to private key")

    args = parser.parse_args()
    logger.info("Arguments successfully read")

    return args.ip, args.username, args.password, args.port, args.key_path


def create_ssh_connection(ip=None, username="root", password=None, port=22, key_path=None):
    ip, username, password, port, key_path = parse_arguments_for_ssh(
        default_ip=ip,
        default_username=username,
        default_password=password,
        default_port=port,
        default_key_path=key_path
    )

    logger.debug("Создаю SSH-client")
    ssh_client = paramiko.SSHClient()

    logger.debug("Загружаю список известных системе серверов")
    ssh_client.load_system_host_keys()
    known_hosts = ssh_client.get_host_keys()

    if ip in known_hosts:
        logger.info(f"Ключ сервера {ip} хранится в known_hosts")
    else:
        logger.warning(f"Ключ сервера {ip} не найден")
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    logger.info(f"Подключаюсь к серверу {ip}")

    for attempt in range(1, 11):  # 10 попыток подключения
        logger.debug(f"Попытка подключения: {attempt}")
        try:
            # Проверка активного соединения
            if ssh_client.get_transport() and ssh_client.get_transport().is_active():
                logger.info("Транспорт уже активен")
                break  # Если подключение уже установлено, выходим из цикла

            if password:
                logger.debug("Пробую подключиться по паролю")
                ssh_client.connect(
                    hostname=ip,
                    port=port,
                    username=username,
                    password=password,
                    allow_agent=False,
                    look_for_keys=False
                )
                logger.info("Подключение по паролю успешно")
                break  # Успешное подключение, выходим из цикла

            elif key_path:
                logger.debug("Пробую подключиться по ssh key")
                ssh_client.connect(
                    hostname=ip,
                    port=port,
                    username=username,
                    key_filename=key_path,
                    allow_agent=False,
                    look_for_keys=False
                )
                logger.info("Подключение по ключу успешно")
                break  # Успешное подключение, выходим из цикла

        except Exception as e:
            logger.error(f"Ошибка подключения на попытке {attempt}: {e}")
            if attempt < 10:
                logger.debug(f"Попытка {attempt} неудачна, ждем перед следующей попыткой...")
                time.sleep(7)  # Задержка перед повторной попыткой
                continue  # Переход к следующей попытке
            else:
                logger.error(f"Не удалось подключиться к серверу {ip} после 10 попыток")
                raise e  # Пробрасываем исключение после последней попытки

    return ssh_client


def closed_ssh_connection(ssh_client, ip=None, username="root", password=None, port=22, key_path=None):
    logger.debug("Получаю информацию о ip сервера")
    ip, username, password, port, key_path = parse_arguments_for_ssh(
        default_ip=ip,
        default_username=username,
        default_password=password,
        default_port=port,
        default_key_path=key_path
    )
    logger.info(f"Закрываю ssh соединение с сервером {ip}")
    try:
        ssh_client.close()
    except Exception as e:
        logging.warning(f"Не удалось закрыть SSH соединение с сервером {ip}")

def create_sftp_connection(ssh_client=None, ip=None, username="root", password=None, port=22, key_path=None):
    logger.debug("Получаю информацию о ip сервера")
    ip, username, password, port, key_path = parse_arguments_for_ssh(
        default_ip=ip,
        default_username=username,
        default_password=password,
        default_port=port,
        default_key_path=key_path
    )

    if ssh_client is None:
        ssh_client = create_ssh_connection()

    logger.info(f"Открываю SFTP соединение с сервером {ip}")

    for attempt in range(1, 11):
        logger.debug(f"Попытка подключения: {attempt}")
        try:
            if ssh_client.get_transport() and ssh_client.get_transport().is_active():
                sftp_client = ssh_client.open_sftp()
                sftp_client.listdir(".")
                logger.info("SFTP соединение успешно установлено")
                return sftp_client
            else:
                logger.error("Для SFTP соединения необходимо SSH соединение")
                break
        except Exception as e:
            logger.warning(f"Попытка {attempt} неуспешного соединения по SFTP: {e}")
            if attempt < 10:
                time.sleep(7)
            else:
                logger.error(f"Не удалось уставноить соединение SFTP с сервером {ip} после 10 попыток")


def close_sftp_connection(sftp_client, ip=None, username="root", password=None, port=22, key_path=None):
    logger.debug("Получаю информацию о ip сервера")
    ip, username, password, port, key_path = parse_arguments_for_ssh(
        default_ip=ip,
        default_username=username,
        default_password=password,
        default_port=port,
        default_key_path=key_path
    )
    logger.info(f"Закрываю ssh соединение с сервером {ip}")
    sftp_client.close()
