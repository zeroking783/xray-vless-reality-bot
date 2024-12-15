from logger import logger
import os
import shutil


def delete_something(path, ssh_client=None):
    logger.info(f"Начинаю удалять {path}")
    if ssh_client is None:
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
            logger.info(f"Пути {path} не существует")
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
                        logger.info(f"Директория {path} успешно удалена")
                    elif stdout_result_type == "file":
                        logger.info(f"Файл {path} успешно удален")
                    else:
                        logger.info(f"Объект {path} успешно удален")
                else:
                    if stdout_result_type == "directory":
                        logger.error(f"Не удалось удалить директорию {path}:\n"
                                      f"{stderr_result}\n"
                                      f"EXIT_CODE: {exit_code}")
                    elif stdout_result_type == "file":
                        logger.error(f"Не удалось удалить файл {path}:\n"
                                      f"{stderr_result}\n"
                                      f"EXIT_CODE: {exit_code}")
                    else:
                        logger.error(f"Не удалось удалить объект {path}:\n"
                                      f"{stderr_result}\n"
                                      f"EXIT_CODE: {exit_code}")
            else:
                logger.error(f"Ошибка при определении объекта (директория/файл) удаления {path}:\n"
                              f"{stderr_result}\n"
                              f"EXIT CODE: {exit_code}")
        if exit_code == 2:
            logger.info(f"Пути {path} не существует")