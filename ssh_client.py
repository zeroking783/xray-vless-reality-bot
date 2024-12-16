import logging
from logger import logger
import argparse
import paramiko
import time

def parse_arguments_for_ssh():
    logger.info("Start parse arguments")
    parser = argparse.ArgumentParser(description="Example Python script to connect to a server")

    parser.add_argument('--ip', type=str, required=True, help='IP address of the server')
    parser.add_argument('--username', type=str, default="root", help='The user for connect to via ssh')
    parser.add_argument('--password', type=str, help='Password for SSH login')
    parser.add_argument('--port', type=int, default=22, help="Port for SSH login")
    parser.add_argument('--key_path', type=str, help="Path to private key")

    args = parser.parse_args()
    logger.info("Arguments successfully read")

    return args.ip, args.username, args.password, args.port, args.key_path

def create_ssh_connection():
    logger.debug("Получаю аргументы запуска кода")
    ip, username, password, port, key_path = parse_arguments_for_ssh()

    logger.debug("Создаю SSH-client")
    ssh_client = paramiko.SSHClient()

    logger.debug("Загружаю список известных системе серверов")
    ssh_client.load_system_host_keys()
    known_hosts = ssh_client.get_host_keys()

    if ip in known_hosts:
        logger.info(f"Ключ сервера {ip} хранится в know_hosts")  
    else:
        logger.warning(f"Ключ сервера {ip} не найден")
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    logger.info(f"Подключаюсь к серверу {ip}")
    for attempt in range(1, 11):
        logger.debug(f"Попытка подключения: {attempt}")
        try:
            if ssh_client.get_transport() and ssh_client.get_transport().is_active():
                break
            if password:
                logger.debug("Пробую подключиться по паролю")
                try:
                    ssh_client.connect(hostname=ip, port=port, username=username, password=password, allow_agent=False,
                                look_for_keys=False)
                except Exception as e:
                    logger.error(f"Не удалось подключиться к серверу {ip} по ssh с помощью пароля:\n {e}")
            if key_path:
                logger.debug("Пробую подключиться по ssh key")
                try:
                    ssh_client.connect(hostname=ip, port=port, username=username, key_filename=key_path, allow_agent=False,
                                    look_for_keys=False)
                except Exception as e:
                    logger.error(f"Не удалось подключиться к серверу {ip} по ssh key:\n {e}")
            logger.info("SSH connection to server successful")
            break
        except Exception as e:
            if attempt < 10:
                logger.debug(f"Connection attempt number {attempt} was unsuccessful: \n{e}")
                time.sleep(7)
            if attempt == 10:
                logger.error(f"Failed to connect to server {ip }via SSH after 10 attempts")

    return ssh_client


def closed_ssh_connection(ssh_client):
    logger.debug("Получаю информацию о ip сервера")
    ip, username, password, port, key_path = parse_arguments_for_ssh()
    logger.info(f"Закрываю ssh соединение с сервером {ip}")
    try:
        ssh_client.close()
    except Exception as e:
        logging.warning(f"Не удалось закрыть SSH соединение с сервером {ip}")

def create_sftp_connection(ssh_client=None):
    logger.debug("Получаю информацию о ip сервера")
    ip, username, password, port, key_path = parse_arguments_for_ssh()

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


def close_sftp_connection(sftp_client):
    logger.debug("Получаю информацию о ip сервера")
    ip, username, password, port, key_path = parse_arguments_for_ssh()
    logger.info(f"Закрываю ssh соединение с сервером {ip}")
    sftp_client.close()