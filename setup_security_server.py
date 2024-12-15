import os
import shutil
import subprocess
import logging
import sys
import socket
import json
import pathlib
import argparse
import random
import secrets
from csv import excel

import paramiko
import configparser
import time
import re
import string
from pathlib import Path


# Обработчик для выхода при ошибках
class ErrorExitHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        if record.levelno >= logging.ERROR:
            sys.exit(1)


# Класс для логгера с контекстом
class ContextualLogger(logging.LoggerAdapter):
    def __init__(self, logger, local_hostname):
        super().__init__(logger, {})
        self.local_hostname = local_hostname

    def process(self, msg, kwargs):
        # Получаем удалённое имя хоста, если передано
        remote_hostname = kwargs.pop("remote_hostname", self.local_hostname)
        # Добавляем контекст локального и удалённого хоста
        return f"[{self.local_hostname} -> {remote_hostname}] {msg}", kwargs


# Основная конфигурация логгера
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

hostname = socket.gethostname()
handler = ErrorExitHandler()

# Формат логов
formatter = logging.Formatter(f'{hostname} - %(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Инициализация обёртки для логгера
context_logger = ContextualLogger(logger, hostname)


def get_new_name_server():
    config = configparser.ConfigParser()

    logging.info("Пытаюсь прочитать инвентарь ansible")
    try:
        config.read('hosts.ini')
    except Exception as e:
        logging.error(f"Ошибка при чтении инвенторя ansible: \n{e}")
    logging.info("Инвентарь ansible успешно прочитан")

    logging.info("Получаю название xray_servers из инвенторя ansible")
    try:
        xray_servers = config.options("xray_servers")
    except Exception as e:
        logging.error(f"Ошибка при получении списка названий xray_servers: \n{e}")
    logging.info("Названия xray_servers успешно считаны")

    number_servers_list = []
    for i in xray_servers:
        server_n = i.split(" ")[0].strip()
        n = server_n.split("-")[1].strip()
        number_servers_list.append(int(n))

    number_servers_list = sorted(number_servers_list)

    for i in range(1, len(number_servers_list)):
        if number_servers_list[i] != number_servers_list[i - 1] + 1:
            new_number = number_servers_list[i - 1] + 1
            new_server_name = "server-" + str(new_number)
            return new_server_name

    new_number = number_servers_list[-1] + 1
    new_server_name = "server-" + str(new_number)
    return new_server_name


def save_information_in_file(directory, name_file, information, create_directory=False, sftp_client=None):
    full_path = pathlib.Path(directory) / name_file

    if create_directory:
        logging.info(f"Start create directory {directory}")
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            logging.error(f"Insufficient permissions to create directory {directory}: \n{e}")
        except Exception as e:
            logging.error(f"Unexpected error creating directory {directory}: \n{e}")
        logging.info(f"Directory {directory} is present/created")

    if sftp_client is not None:
        logging.info(f"I start writing to file {full_path} on the remote server")
        try:
            with sftp_client.open(str(full_path), 'w') as file:
                file.write(information)
        except PermissionError as e:
            logging.error(f"Insufficient permissions to write to file {full_path}: \n{e}")
        except Exception as e:
            logging.error(f"Unexpected error writing to file {full_path}: \n{e}")
        logging.info(f"{full_path} successfully written")
    else:
        try:
            with open(full_path, "w") as file:
                file.write(information)
        except PermissionError as e:
            logging.error(f"Insufficient permissions to write to file {full_path}: \n{e}")
        except Exception as e:
            logging.error(f"Unexpected error writing to file {full_path}: \n{e}")
        logging.info(f"{full_path} successfully written")


def generate_ssh_login():

    port = random.randint()

def parse_arguments():
    logging.info("Start parse arguments")
    parser = argparse.ArgumentParser(description="Example Python script to connect to a server")

    parser.add_argument('--ip', type=str, required=True, help='IP address of the server')
    parser.add_argument('--password', type=str, required=True, help='Password for SSH login')

    args = parser.parse_args()
    logging.info("Arguments successfully read")

    return args.ip, args.password


def change_string_with_regular(directory, name_file, regular, string_after, sftp_client=None):
    full_path = pathlib.Path(directory) / name_file

    if sftp_client is None:
        logging.info(f"Начинаю читать файл {full_path} на этой машине")
        try:
            with open(full_path, "r") as file:
                lines = file.readlines()
        except Exception as e:
            logging.error(f"Ошибка при чтении файла {full_path}: \n{e}")
        logging.info(f"Файл {full_path} успешно прочитан")
    else:
        logging.info(f"Начинаю читать файл {full_path} на удаленной машине")
        try:
            with sftp_client.open(str(full_path), "r") as file:
                lines = file.readlines()
        except Exception as e:
            logging.error(f"Ошибка при чтении файла {full_path}: \n{e}")
        logging.info(f"Файл {full_path} успешно прочитан")

    pattern = re.compile(regular)
    updated_lines = []
    for line in lines:
        if pattern.match(line):
            updated_lines.append(f"{string_after}\n")
        else:
            updated_lines.append(line)

    if sftp_client is None:
        logging.info(f"Начинаю записывать файл {full_path} на этой машине")
        try:
            with open(full_path, "w") as file:
                file.writelines(updated_lines)
        except Exception as e:
            logging.error(f"Ошибка при записи файла {full_path}: \n{e}")
        logging.info(f"Файл {full_path} успешно записан")
    else:
        logging.info(f"Начинаю записывать файл {full_path} на удаленной машине")
        try:
            with sftp_client.open(str(full_path), "w") as file:
                file.writelines(updated_lines)
        except Exception as e:
            logging.error(f"Ошибка при записи файла {full_path}: \n{e}")
        logging.info(f"Файл {full_path} успешно записан")


def restart_server_service(service_name, ssh_client=None):
    command_restart = f"sudo systemctl restart {service_name}"

    if ssh_client is not None:
        logging.info(f"Выполняю команду перезагрузки службы {service_name} на удаленном сервере")
        stdin, stdout, stderr = ssh_client.exec_command(command_restart)

        stdout_result = stdout.read().decode().strip()
        stderr_result = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()

        if exit_code == 0:
            logging.info("Перезагрузка службы {service_name} прошла успешно")
            logging.debug(f"shortIds: \n{stdout_result}")
        else:
            logging.error("Ошибка перезагрузки службы: \n"
                          f"{stderr_result}"
                          f"exit_code: {exit_code}\n")
    else:
        logging.info(f"Выполняю команду перезагрузки службы {service_name} на этой машине")
        result_command = subprocess.run(command_restart, shell=True, capture_output=True, text=True)

        stdout_result = result_command.stdout
        stderr_result = result_command.stderr
        exit_code = result_command.returncode

        if exit_code == 0:
            logging.info("Перезагрузка службы {service_name} прошла успешно")
            logging.debug(f"shortIds: \n{stdout_result}")
        else:
            logging.error("Ошибка перезагрузки службы: \n"
                          f"{stderr_result}"
                          f"exit_code: {exit_code}\n")


def create_user(password, username="xray", ssh_client=None):

    command = f"useradd -m -U -s /bin/bash -p $(openssl passwd -1 '{password}') {username}"

    if ssh_client is not None:
        logging.info("Создаю пользователя на удаленном сервере")
        stdin, stdout, stderr = ssh_client.exec_command(command)

        stdout_result = stdout.read().decode().strip()
        stderr_result = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()

        if exit_code == 0:
            logging.info("Пользователь успешно создался ")
            logging.debug(f"stdout: \n{stdout_result}")
        else:
            logging.error("Ошибка при создании пользователя: \n"
                          f"{stderr_result}"
                          f"exit_code: {exit_code}\n")
    else:
        logging.info("Создаю пользователя на этой машине")
        result_command = subprocess.run(command, shell=True, capture_output=True, text=True)

        stdout_result = result_command.stdout
        stderr_result = result_command.stderr
        exit_code = result_command.returncode

        if exit_code == 0:
            logging.info("Пользователь успешно создался")
            logging.debug(f"stdout: \n{stdout_result}")
        else:
            logging.error("Ошибка при создании пользователя: \n"
                          f"{stderr_result}"
                          f"exit_code: {exit_code}\n")

def generate_random_string(length=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))

def generate_password():
    logging.info("Генерирую пароль")
    password = generate_random_string(12, string.ascii_letters + string.digits + string.punctuation)
    return password


def delete_something(path, ssh_client=None):
    logging.info(f"Начинаю удалять {path}")
    if ssh_client is None:
        if os.path.exists(path):
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path)
                    logging.info(f"Директория {path} успешно удалена")
                except Exception as e:
                    logging.error(f"Не удалось удалить директорию {path}:\n {e}")
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    logging.info(f"Файл {path} успешно удален")
                except Exception as e:
                    logging.error(f"Не удалось удалить файл {path}:\n {e}")
        else:
            logging.info(f"Пути {path} не существует")
    else:
        command_check_type = f"""
                if [ -d "{path}" ]; then echo directory; \
                elif [ -f "{path}" ]; then echo file; \
                else echo other; fi
                """
        command_delete = f"rm -rf {path}"
        command_check_exist = f"ls {path}"

        stdin, stdout, stderr = ssh_client.exec_command(command_check_exist)
        exit_code = stdout.channel.recv_exit_status()

        if exit_code == 0:
            stdin, stdout, stderr = ssh_client.exec_command(command_check_type)
            stdout_result_type = stdout.read().decode().strip()
            stderr_result = stderr.read().decode()
            exit_code = stdout.channel.recv_exit_status()

            if exit_code == 0:
                stdin, stdout, stderr = ssh_client.exec_command(command_delete)
                stderr_result = stderr.read().decode()
                exit_code = stdout.channel.recv_exit_status()

                if exit_code == 0:
                    if stdout_result_type == "directory":
                        logging.info(f"Директория {path} успешно удалена")
                    elif stdout_result_type == "file":
                        logging.info(f"Файл {path} успешно удален")
                    else:
                        logging.info(f"Объект {path} успешно удален")
                else:
                    if stdout_result_type == "directory":
                        logging.error(f"Не удалось удалить директорию {path}:\n"
                                      f"{stderr_result}\n"
                                      f"EXIT_CODE: {exit_code}")
                    elif stdout_result_type == "file":
                        logging.error(f"Не удалось удалить файл {path}:\n"
                                      f"{stderr_result}\n"
                                      f"EXIT_CODE: {exit_code}")
                    else:
                        logging.error(f"Не удалось удалить объект {path}:\n"
                                      f"{stderr_result}\n"
                                      f"EXIT_CODE: {exit_code}")
            else:
                logging.error(f"Ошибка при определении объекта (директория/файл) удаления {path}:\n"
                              f"{stderr_result}\n"
                              f"EXIT CODE: {exit_code}")
        if exit_code == 2:
            logging.info(f"Пути {path} не существует")



def create_something(path, ssh_client=None, recreate=False):
    logging.info(f"Создаю директорию {path}")
    if ssh_client is None:
        try:
            if recreate == True:
                if os.path.exists(path):
                    try:
                        shutil.rmtree(path)
                        logging.debug(f"Директория {path} успешно удалена")
                    except Exception as e:
                        logging.error(f"Не удалось удалить директорию {path}:\n {e}")
            os.makedirs(path, exist_ok=True)
            logging.info(f"Директория {path} успешно создана")
        except Exception as e:
            logging.error(f"Ошибка при создании директории {path}:\n {e}")
    else:
        command_create_directory = f""


def create_ssh_keys_connection(ssh_client, sftp_client, server_name):
    logging.info(f"Начинаю создавать подлючение по ssh keys")

    command_create_keys = f"ssh-keygen -t rsa -b 4096 -f /home/bakvivas/.ssh/xray/{server_name} -N ''"


logging.info("Initializing the creation of an ssh connection")
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ip, password_ssh = parse_arguments()
print(ip, password_ssh)

logging.info("I try to connect to the server several times")
for attempt in range(1, 11):
    logging.debug(f"Connection attempts: {attempt}")
    try:
        if ssh_client.get_transport() and ssh_client.get_transport().is_active():
            logging.info("SSH connection is already active. Exiting attempts loop.")
            break
        ssh_client.connect(hostname=ip, port=22, username='root', password=password_ssh, allow_agent=False, look_for_keys=False)
        logging.info("SSH connection to server successful")
        break
    except Exception as e:
        if attempt < 10:
            logging.debug(f"Connection attempt number {attempt} was unsuccessful: \n{e}")
            time.sleep(7)
        if attempt == 10:
            logging.error(f"Failed to connect to server via SSH after 10 attempts")

new_server_name = get_new_name_server()

sftp_client = ssh_client.open_sftp()

#  Меняю название сервера
save_information_in_file("/etc", "hostname", new_server_name, create_directory=False, sftp_client=sftp_client)

# Пробрасываю другой порт
port_number = random.randint(20000, 65000)
port_string = "Port=" + str(port_number)
print(port_string)
change_string_with_regular("/etc/ssh", "sshd_config", r"^#?Port\s+\d+", port_string, sftp_client=sftp_client)

# Рестарт службы ssh
restart_server_service("ssh", ssh_client=ssh_client)

# Добавляю пользователя xray со сгенерированным паролем
password = generate_password()
create_user(password, username="xray", ssh_client=ssh_client)

# Отключаем подключение к root по ssh
change_string_with_regular("/etc/ssh", "sshd_config", r"^PermitRootLogin\s+(yes|no)", "PermitRootLogin no", sftp_client)

# Рестарт службы ssh
restart_server_service("ssh", ssh_client=ssh_client)

# Создаю пару ключей ssh и закидываю на сервер



sftp_client.close()
ssh_client.close()




