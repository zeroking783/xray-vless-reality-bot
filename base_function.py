from logger import logger
import os
import shutil
import re
import subprocess
import crypt
from ssh_client import create_sftp_connection, close_sftp_connection
import random
import string
import configparser


def get_remote_ip(ssh_client):
    logger.info(f"Получаю ip сервера по ssh_client")
    stdin, stdout, stderr = ssh_client.exec_command("hostname -I")
    remote_ip = stdout.read().decode().strip()
    logger.info(f"ip сервера успешно получен")
    return remote_ip


def delete_something(path, ssh_client=None):

    if ssh_client is None:
        logger.info(f"Удаляю {path}")
        if os.path.exists(path):
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path)
                    logger.info(f"Директория {path} успешно удалена")
                except Exception as e:
                    logger.error(f"Не удалось удалить директорию {path}:\n {e}")
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    logger.info(f"Файл {path} успешно удален")
                except Exception as e:
                    logger.error(f"Не удалось удалить файл {path}:\n {e}")
        else:
            logger.debug(f"Пути {path} не существует")
    else:
        remote_ip = get_remote_ip(ssh_client)
        logger.info(f"Удаляю {path}", remote_ip=remote_ip)
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
                        logger.info(f"Директория {path} успешно удалена", remote_ip=remote_ip)
                    elif stdout_result_type == "file":
                        logger.info(f"Файл {path} успешно удален", remote_ip=remote_ip)
                    else:
                        logger.info(f"Объект {path} успешно удален", remote_ip=remote_ip)
                else:
                    if stdout_result_type == "directory":
                        logger.error(f"Не удалось удалить директорию {path}:\n"
                                      f"{stderr_result}\n"
                                      f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
                    elif stdout_result_type == "file":
                        logger.error(f"Не удалось удалить файл {path}:\n"
                                      f"{stderr_result}\n"
                                      f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
                    else:
                        logger.error(f"Не удалось удалить объект {path}:\n"
                                      f"{stderr_result}\n"
                                      f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
            else:
                logger.error(f"Ошибка при определении объекта (директория/файл) удаления {path}:\n"
                              f"{stderr_result}\n"
                              f"EXIT CODE: {exit_code}", remote_ip=remote_ip)
        if exit_code == 2:
            logger.debug(f"Пути {path} не существует", remote_ip=remote_ip)


def create_something(path, is_file=False, ssh_client=None, recreate=False):

    path_list = path.strip().split("/")[1:]
    parent_path = "/" + "/".join(path_list[:-1])

    if "." in path_list[-1]:
        is_file = True

    if ssh_client:
        remote_ip = get_remote_ip(ssh_client)
        logger.info(f"Начинаю создавать {path}", remote_ip=remote_ip)
        if recreate:
            logger.debug(f"Директория {path} будет пересоздана", remote_ip=remote_ip)
            command_delete = f"rm -rf {path}"
            stdin, stdout, stderr = ssh_client.exec_command(command_delete)
            exit_code = stdout.channel.recv_exit_status()
            stderr_result = stderr.read().decode()
            if exit_code != 0:
                logger.error(f"Что-то пошло не так при удалении директории {path} при пересоздании:\n"
                             f"{stderr_result}\n"
                             f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
        else:
            command_check_type = f"""
                            if [ -d "{path}" ]; then echo directory; \
                            elif [ -f "{path}" ]; then echo file; \
                            else echo unknown; fi
                            """
            stdin, stdout, stderr = ssh_client.exec_command(command_check_type)
            stdout_result_type = stdout.read().decode().strip()
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                if stdout_result_type == "directory" and is_file:
                    logger.error(f"Вы пытаетесь пересоздать директорию {path} в файл", remote_ip=remote_ip)
                elif stdout_result_type == "file" and is_file == False:
                    logger.error(f"Вы пытаетесь пересоздать файл {path} в директорию", remote_ip=remote_ip)

        command_makedir_parrent = f"mkdir -p {parent_path}"
        logger.debug(f"Создаю промежуточный путь {parent_path}", remote_ip=remote_ip)
        stdin, stdout, stderr = ssh_client.exec_command(command_makedir_parrent)
        exit_code = stdout.channel.recv_exit_status()
        stderr_result = stderr.read().decode()
        if exit_code == 0:
            logger.debug(f"Промежуточный путь {parent_path} создался/существовал", remote_ip=remote_ip)
        else:
            logger.error(f"Неизвестная ошибка при создании промежуточного пути:\n"
                         f"{stderr_result}\n"
                         f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
        if is_file:
            command_mkfile = f"touch {path}"
            stdin, stdout, stderr = ssh_client.exec_command(command_mkfile)
            exit_code = stdout.channel.recv_exit_status()
            stderr_result = stderr.read().decode()
            if exit_code == 0:
                logger.info(f"Файл {path} успешно создался", remote_ip=remote_ip)
            elif exit_code == 1:
                logger.info(f"Файл {path} уже существует", remote_ip=remote_ip)
            else:
                logger.error(f"Не удалось создать файл {path}:\n"
                             f"{stderr_result}\n"
                             f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
        else:
            command_mkdir = f"mkdir {path}"
            stdin, stdout, stderr = ssh_client.exec_command(command_mkdir)
            exit_code = stdout.channel.recv_exit_status()
            stderr_result = stderr.read().decode()
            if exit_code == 0:
                logger.info(f"Директория {path} успешно создана", remote_ip=remote_ip)
            elif exit_code == 1:
                logger.info(f"Директория {path} уже существует", remote_ip=remote_ip)
            else:
                logger.error(f"Не удалось создать директорию {path}:\n"
                             f"{stderr_result}\n"
                             f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
    else:
        logger.info(f"Начинаю создавать {path}")
        if os.path.exists(path):
            if os.path.isdir(path) and is_file is False:
                logger.debug(f"Директория {path} уже существует")
                if recreate == True:
                    logger.info(f"Пересоздаю директорию {path}")
                    delete_something(path)
                    try:
                        os.makedirs(path)
                        logger.info(f"Директория {path} успешно пересоздалась")
                    except Exception as e:
                        logger.error(f"Не удалось пересоздать директорию {path}: \n {e}")
                else:
                    logger.debug(f"Директория {path} уже существует")
            elif os.path.isfile(path) and is_file:
                if recreate == True:
                    logger.debug(f"Пересоздаю файл {path}")
                    delete_something(path)
                    try:
                        with open(path, "w") as file:
                            pass
                        logger.info(f"Файл {path} успешно создан")
                    except Exception as e:
                        logger.error(f"Не удалось пересоздать файл {path}: \n {e}")
                else:
                    logger.debug(f"Файл {path} уже существует")
            elif os.path.isdir(path) and is_file is True:
                logger.error(f"Вы хотите создать файл {path}, но уже существует такая директория")
            elif os.path.isfile(path) and is_file is False:
                logger.error(f"Вы хотите создать директорию {path}, но уже существует такой файл")
        else:
            if is_file is False:
                try:
                    os.makedirs(path)
                    logger.info(f"Директория {path} успешно создалась")
                except Exception as e:
                    logger.error(f"Не удалось создать директорию {path}: \n {e}")
            else:
                directory = os.path.dirname(path)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                try:
                    with open(path, "w") as file:
                        pass
                    logger.info(f"Файл {path} успешно создался")
                except Exception as e:
                    logger.error(f"Не удалось создать файл {path}: \n {e}")


def check_exists_something(path, ssh_client=None):

    if ssh_client:
        remote_ip = get_remote_ip(ssh_client)
        logger.info(f"Начинаю проверять наличие {path}", remote_ip=remote_ip)

        command_check_exist = f"test -e {path} && echo 'exists' || echo 'not_exists'"
        stdin, stdout, stderr = ssh_client.exec_command(command_check_exist)
        exit_code = stdout.channel.recv_exit_status()
        stdout_result = stdout.read().decode().strip()
        stderr_result = stderr.read().decode()

        if exit_code == 0:
            logger.debug(f"Поиск файла {path} выполнен успешно", remote_ip=remote_ip)
            if stdout_result == "exists":
                logger.info(f"Файл {path} существует", remote_ip=remote_ip)
                return True
            else:
                logger.info(f"Файла {path} не существует", remote_ip=remote_ip)
                return  False
        else:
            logger.error(f"Не удалось выполнить поиск файла:\n"
                         f"{stderr_result}\n"
                         f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
    else:
        logger.info(f"Начинаю проверять наличие {path}")

        command_check_exist = f"test -e '{path}' && echo 'exists' || echo 'not_exists'"
        result_command = subprocess.run(command_check_exist, shell=True, capture_output=True, text=True)
        stderr_result = result_command.stderr
        exit_code = result_command.returncode
        stdout_result = result_command.stdout.strip()

        if exit_code == 0:
            logger.debug(f"Поиск файла {path} выполнен успешно")
            if stdout_result == "exists":
                logger.info(f"Файл {path} существует")
                return True
            else:
                logger.info(f"Файла {path} не существует")
                return False
        else:
            logger.error(f"Не удалось выполнить поиск файла:\n"
                         f"{stderr_result}\n"
                         f"EXIT_CODE: {exit_code}")


def change_string_in_file(path, regular, string_after, ssh_client=None):

    sftp_client = None

    if ssh_client:
        remote_ip = get_remote_ip(ssh_client)
        logger.info(f"Начинаю изменять строку {regular} в файле {path} на {string_after}", remote_ip=remote_ip)
        sftp_client = create_sftp_connection(ssh_client)
        logger.debug(f"Начинаю читать файл {path}", remote_ip=remote_ip)
        try:
            with sftp_client.open(str(path), "r") as file:
                lines = file.readlines()
            logger.debug(f"Файл {path} успешно прочитан", remote_ip=remote_ip)
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {path}: \n{e}", remote_ip=remote_ip)
    else:
        logger.info(f"Начинаю изменять строку {regular} в файле {path} на {string_after}")
        logger.debug(f"Начинаю читать файл {path}")
        try:
            with open(path, "r") as file:
                lines = file.readlines()
                logger.debug(f"Файл {path} успешно прочитан")
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {path}: \n{e}")

    file_edited = False

    logger.debug(f"Изменяю данные в файле {path}")
    updated_lines = []
    try:
        pattern = re.compile(regular)
        for line in lines:
            if pattern.match(line):
                updated_lines.append(f"{string_after}\n")
                file_edited = True
            else:
                updated_lines.append(line)
    except Exception as e:
        logger.error(f"Ошибка при изменении данных в файле {path}:\n {e}")

    if file_edited:
        logger.debug(f"Файл {path} согласно заданным параметрам")
    else:
        logger.debug(f"В файле {path} не нашлось заданного регулярного выражения")

    if ssh_client:
        remote_ip = get_remote_ip(ssh_client)
        logger.debug(f"Начинаю записывать данные в файл {path}", remote_ip=remote_ip)
        try:
            with sftp_client.open(str(path), "w") as file:
                file.writelines(updated_lines)
        except Exception as e:
            logger.error(f"Ошибка при записи файла {path}: \n{e}", remote_ip=remote_ip)
        logger.info(f"Файл {path} успешно записан", remote_ip=remote_ip)
        close_sftp_connection(sftp_client)
    else:
        logger.debug(f"Начинаю записывать данные в файл {path}")
        try:
            with open(path, "w") as file:
                file.writelines(updated_lines)
        except Exception as e:
            logger.error(f"Ошибка при записи файла {path}: \n{e}")
        logger.info(f"Файл {path} успешно записан")


def restart_service(service, ssh_client=None):

    if ssh_client:
        remote_ip = get_remote_ip(ssh_client)
        logger.info(f"Начинаю перезагружать службу {service}", remote_ip=remote_ip)

        command_restart = f"systemctl restart {service}"
        stdin, stdout, stderr = ssh_client.exec_command(command_restart)
        exit_code = stdout.channel.recv_exit_status()
        stderr_result = stderr.read().decode()

        if exit_code == 0:
            logger.info(f"Сервис {service} успешно перезагружке", remote_ip=remote_ip)
        else:
            logger.error(f"Ошибка при перезагружке сервера:\n "
                         f"{stderr_result}\n"
                         f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
    else:
        logger.info(f"Выполняю команду перезагрузки службы {service}")

        command_restart = ["systemctl", "restart", service]
        result_command = subprocess.run(command_restart, capture_output=True, text=True)
        stderr_result = result_command.stderr
        exit_code = result_command.returncode

        if exit_code == 0:
            logger.info(f"Перезагрузка службы {service} прошла успешно")
        else:
            logger.error("Ошибка перезагрузки службы: \n"
                          f"{stderr_result}\n"
                          f"EXIT_CODE: {exit_code}")


def create_user(password, username, ssh_client=None):

    hashed_password = None

    if ssh_client:
        remote_ip = get_remote_ip(ssh_client)
        logger.info(f"Создаю нового пользователя {username}", remote_ip=remote_ip)

        logger.debug(f"Хэширую пароль", remote_ip=remote_ip)
        try:
            hashed_password = crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))
            logger.debug(f"Пароль успешно захэширован", remote_ip=remote_ip)
        except Exception as e:
            logger.error(f"Хэширование пароля закончилось с ошибкой", remote_ip=remote_ip)

        command_create_user = f"useradd -m -U -s /bin/bash -p '{hashed_password}' {username}"
        stdin, stdout, stderr = ssh_client.exec_command(command_create_user)
        exit_code = stdout.channel.recv_exit_status()
        stderr_result = stderr.read().decode()

        if exit_code == 0:
            logger.info(f"Пользователь {username} успешно создан", remote_ip=remote_ip)
        else:
            logger.error(f"Ошибка при создании пользователя {username}:\n"
                         f"{stderr_result}\n"
                         f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
    else:
        logger.info(f"Создаю нового пользователя {username}")

        logger.debug(f"Хэширую пароль")
        try:
            hashed_password = crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))
            logger.debug(f"Пароль успешно захэширован")
        except Exception as e:
            logger.error(f"Хэширование пароля закончилось с ошибкой")

        command_create_user = ["useradd", "-m", "-U", "-s", "/bin/bash", "-p", hashed_password, username]
        result_command = subprocess.run(command_create_user, capture_output=True, text=True)
        stderr_result = result_command.stderr
        exit_code = result_command.returncode

        if exit_code == 0:
            logger.info(f"Пользователь {username} успешно создан")
        else:
            logger.error(f"Ошибка при создании пользователя {username}:\n"
                         f"{stderr_result}\n"
                         f"EXIT_CODE: {exit_code}")


def generate_random_string(length=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))


def generate_password():
    logger.info("Генерирую пароль")
    password = generate_random_string(16, string.ascii_letters + string.digits + string.punctuation)
    logger.info("Пароль сгенерирован")
    return password


def create_ssh_keys(key_name, directory="/home/xray/.ssh", recreate=False):

    logger.info(f"Создаю пару ssh ключей {key_name} в директории {directory}")

    path = directory + "/" + key_name
    logger.debug(f"Полный путь к ключу: {path}")

    if check_exists_something(path):
        if recreate:
            logger.debug(f"Пересоздаю ключ {path}")
            delete_something(path)
            delete_something(path+".pub")
        else:
            logger.error(f"Ключ {path} уже существует, нет прав к пересозданию")

    # ssh-keygen -t rsa -b 4096 -f /home/xray/.ssh/server-1 -N ''
    command_create_keys = ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", path, "-N", '']
    result_command = subprocess.run(command_create_keys, capture_output=True, text=True, stdin=subprocess.PIPE)
    stderr_result = result_command.stderr
    exit_code = result_command.returncode

    print('au')

    if exit_code == 0:
        logger.info(f"SSH ключи созданы успешно")
    else:
        logger.error(f"Ошибка при создании пары SSH ключей:\n"
                     f"{stderr_result}\n"
                     f"EXIT_CODE: {exit_code}")


def check_premissions(path, ssh_client=None):
    if ssh_client:
        remote_ip = get_remote_ip(ssh_client)
        logger.info(f"Получаю права доступа на файл {path}", remote_ip=remote_ip)

        file_exists = check_exists_something(path, ssh_client=ssh_client)

        if file_exists is False:
            logger.error(f"Файла {path} не существует", remote_ip=remote_ip)
            return None

        command_check_premissions = f"stat -c %a {path}"
        stdin, stdout, stderr = ssh_client.exec_command(command_check_premissions)
        exit_code = stdout.channel.recv_exit_status()
        stdout_result = stdout.read().decode().strip()
        stderr_result = stderr.read().decode()

        if exit_code == 0:
            logger.info(f"Файл {path} имеет права доступа {stdout_result}", remote_ip=remote_ip)
            return stdout_result
        else:
            logger.error(f"Не удалось получить права доступа на файл {path}:\n"
                         f"{stderr_result}\n"
                         f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
            return None
    else:
        logger.info(f"Получаю права доступа на файл {path}")

        file_exists = check_exists_something(path)

        if file_exists is False:
            logger.error(f"Файла {path} не существует")
            return None

        command_check_premissions = ["stat", "-c", "%a", path]
        result_command = subprocess.run(command_check_premissions, capture_output=True, text=True)
        stderr_result = result_command.stderr
        stdout_result = result_command.stdout
        exit_code = result_command.returncode

        if exit_code == 0:
            logger.info(f"Файл {path} имеет права доступа {stdout_result}")
            return stdout_result
        else:
            logger.error(f"Не удалось получить права доступа на файл {path}:\n"
                         f"{stderr_result}\n"
                         f"EXIT_CODE: {exit_code}")
            return None


def change_premissions(path, right, recursion=True, ssh_client=None):
    if ssh_client:
        remote_ip = get_remote_ip(ssh_client)
        logger.info(f"Изменяю права доступа на файл {path} на {right}", remote_ip=remote_ip)

        file_exists = check_exists_something(path, ssh_client=ssh_client)

        if file_exists is False:
            logger.error(f"Файла {path} не существует", remote_ip=remote_ip)
            return None

        premissions_now = check_premissions(path, ssh_client)
        if premissions_now == right:
            logger.info(f"Файл {path} уже имеет права доступа {right}", remote_ip=remote_ip)
            return None

        if recursion:
            command_change_premissions = f"chmod -R {right} {path}"
            logger.debug(f"Права будут изменяться рекурсивно", remote_ip=remote_ip)
        else:
            command_change_premissions = f"chmod {right} {path}"
            logger.debug(f"Права будут изменяться не рекурсивно", remote_ip=remote_ip)
        stdin, stdout, stderr = ssh_client.exec_command(command_change_premissions)
        exit_code = stdout.channel.recv_exit_status()
        stderr_result = stderr.read().decode()

        if exit_code == 0:
            logger.info(f"Права доступа на файл {path} успешно изменены на {right}", remote_ip=remote_ip)
        else:
            logger.error(f"Ошибка при попытке изменить права доступа файла {path} на {right}:\n"
                         f"{stderr_result}\n"
                         f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
    else:
        file_exists = check_exists_something(path)

        if file_exists is False:
            logger.error(f"Файла {path} не существует")
            return None

        premissions_now = check_premissions(path)
        if premissions_now == right:
            logger.info(f"Файл {path} уже имеет права доступа {right}")
            return None

        if recursion:
            command_change_premissions = ["chmod", "-R", right, path]
            logger.debug(f"Права будут изменяться рекурсивно")
        else:
            command_change_premissions = ["chmod", right, path]
            logger.debug(f"Права будут изменяться не рекурсивно")
        result_command = subprocess.run(command_change_premissions, capture_output=True, text=True)
        stderr_result = result_command.stderr
        exit_code = result_command.returncode

        if exit_code == 0:
            logger.info(f"Права доступа на файл {path} успешно изменены на {right}")
        else:
            logger.error(f"Ошибка при попытке изменить права доступа файла {path} на {right}:\n"
                         f"{stderr_result}\n"
                         f"EXIT_CODE: {exit_code}")


def users_list(ssh_client=None):
    if ssh_client:
        remote_ip = get_remote_ip(ssh_client)
        logger.info(f"Начинаю читать список пользователей", remote_ip=remote_ip)
        sftp_client = create_sftp_connection(ssh_client)

        logger.debug(f"Создаю список со всеми пользователями", remote_ip=remote_ip)
        try:
            with sftp_client.open("/etc/passwd", "r") as passwd_file:
                users = []
                for line in passwd_file:
                    user = line.split(":")[0]
                    users.append(user)
                logger.info(f"Пользователи из файла /etc/passwd успешно прочитаны", remote_ip=remote_ip)
                return users
        except Exception as e:
            logger.error(f"Произошла ошибка при чтении /etc/passwd:\n {e}", remote_ip=remote_ip)
    else:
        logger.info(f"Начинаю читать список пользователей")
        logger.debug(f"Создаю список со всеми пользователями")
        try:
            with open("/etc/passwd", "r") as passwd_file:
                users = []
                for line in passwd_file:
                    user = line.split(":")[0]
                    users.append(user)
                logger.info(f"Пользователи из файла /etc/passwd успешно прочитаны")
                return users
        except Exception as e:
            logger.error(f"Произошла ошибка при чтении /etc/passwd:\n {e}")


def get_free_name_server(path="/home/xray/xray-vless-reality-bot/hosts.ini"):
    xray_servers = None
    logger.info(f"Получаю незанятое имя для сервера")

    logger.debug(f"Запускаю парсер конфигов")
    config = configparser.ConfigParser()

    logger.debug(f"Пытаюсь прочитать инвентарь ansible")
    try:
        config.read(path)
        logger.debug(f"Инвентарь ansible успешно прочитан")
    except Exception as e:
        logger.error(f"Ошибка при чтении инвенторя ansible")

    logger.debug(f"Пытаюсь получить названия серверов в инвенторе ansible")
    try:
        xray_servers = config.options("xray_servers")
        logger.debug(f"Названия всех серверов xray_servers успешно прочитаны")
    except Exception as e:
        logger.error(f"Ошибка при получении списка названий серверов xray_servers в инвенторе ansible: \n{e}")

    logger.debug(f"Записываю номера занятых серверов и сортирую их")
    number_servers_list = []
    for i in xray_servers:
        server_n = i.split(" ")[0].strip()
        n = server_n.split("-")[1].strip()
        number_servers_list.append(int(n))
    number_servers_list = sorted(number_servers_list)

    logger.debug(f"Начинаю переберать номера серверов, для поиска свободного")
    for i in range(1, len(number_servers_list)):
        if number_servers_list[i] != number_servers_list[i - 1] + 1:
            new_number = number_servers_list[i - 1] + 1
            new_server_name = "server-" + str(new_number)
            logger.info(f"Найдено свободное имя для сервера: {new_server_name}")
            return new_server_name
    logger.error(f"Не найдено свободное имя для сервера")


def transfer_ssh_key(key_name, ssh_client, remote_directory, local_directory="/home/xray/.ssh"):
    public_key_path = local_directory + "/" + key_name + ".pub"

    with open(public_key_path, 'r') as pub_key_file:
        public_key = pub_key_file.read().strip()

    create_something()

    create_sftp_connection(ssh_client)


def write_data_in_file(path, data, recreate=False, ssh_client=None):
    if ssh_client:
        remote_ip = get_remote_ip(ssh_client)
        logger.info(f"Начинаю записывать информацию {data} в файл {path}", remote_ip=remote_ip)

        write_mode = '>' if recreate else '>>'

        logger.debug(f"Использую режим записи {write_mode} для файла {path}", remote_ip=remote_ip)
        command_write_in_file = f"echo '{data}' {write_mode} {path}"
        stdin, stdout, stderr = ssh_client.exec_command(command_write_in_file)
        exit_code = stdout.channel.recv_exit_status()
        stderr_result = stderr.read().decode()

        if exit_code == 0:
            logger.info(f"Информация {data} была успешно записана в файл {path} способом {write_mode}", remote_ip=remote_ip)
        else:
            logger.error(f"Произошла ошибка при записи {data} в файл {path} способом {write_mode}:\n "
                         f"{stderr_result}\n"
                         f"EXIT_CODE: {exit_code}", remote_ip=remote_ip)
    else:
        logger.info(f"Начинаю записывать данные {data} в файл {path}")

        write_mode = 'w' if recreate else 'a'
        logger.debug(f"Использую режим записи {write_mode} для файла {path}")
        try:
            with open(path, write_mode) as file:
                file.write(data)
            logger.info(f"Информация {data} была успешно записана в файл {path} способом {write_mode}")
        except Exception as e:
            logger.error(f"Произошла ошибка при записи {data} в файл {path} способом {write_mode}:\n {e}")
