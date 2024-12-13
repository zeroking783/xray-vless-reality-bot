import json
import logging
import socket
import subprocess
import pathlib


class ErrorExitHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        if record.levelno >= logging.ERROR:
            sys.exit(1)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

hostname = socket.gethostname()
handler = ErrorExitHandler()
formatter = logging.Formatter(f'{hostname} - %(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Just generate uuid
def create_uuid(email):
    logging.info(f"I enter the command to get the uuid for user {email}")
    command_get_uuid = "/usr/local/bin/xray uuid"
    result_command_get_uuid = subprocess.run(command_get_uuid, shell=True, capture_output=True, text=True)

    stdout_result_command_get_uuid = result_command_get_uuid.stdout
    stderr_result_command_get_uuid = result_command_get_uuid.stderr
    exit_code_result_command_get_uuid = result_command_get_uuid.returncode

    if exit_code_result_command_get_uuid == 0:
        logging.info("uuid received successfully")
        logging.debug(f"uuid: \n{stdout_result_command_get_uuid}")
    else:
        logging.error(f"Error while getting uuid: \n"
                      f"{stderr_result_command_get_uuid}\n"
                      f"exit_code: {exit_code_result_command_get_uuid}")
    logging.info("uuid successfully generated")

    return stdout_result_command_get_uuid


def get_old_config_xray():
    logging.info("Took xray config for processing")
    xray_config_path = "/usr/local/etc/xray/config.json"
    try:
        with open(xray_config_path, "r") as json_file:
            xray_config_json = json.load(json_file)
    except PermissionError as e:
        logging.error(f"Недостаточно прав для чтения конфигурационного файла xray: \n{e}")
    except Exception as e:
        logging.error(f"Ошибка при попытке чтения конфигурационного файла xray: \n{e}")

    logging.info("Конфигурационный файл xray успешно прочитан")
    return xray_config_json


def save_new_config_xray(xray_config_new):

    save_directory = "/usr/local/etc/xray"
    xray_config_path = pathlib.Path(save_directory) / "config.json"

    try:
        with open(xray_config_path, "w") as file:
            file.write(xray_config_new)
    except PermissionError as e:
        logging.error(f"Insufficient permissions to write to file: \n{e}")
    except Exception as e:
        logging.error(f"Unexpected error writing to file: \n{e}")
    logging.info("New user successfully added to xray config")


# Это общая функция для добавления пользователя в конфигурацию xray
def add_client(email):

    uuid = create_uuid(email)

    new_client = {
        "id": uuid,
        "email": "email",
        "flow": "xtls-rprx-vision"
    }

    xray_config_old_json = get_old_config_xray()
    xray_config_new_json = xray_config_old_json
    xray_config_new_json["inbounds"][0]["settings"]["clients"].append(new_client)

    xray_config_new = json.dumps(xray_config_new_json, sort_keys=True, indent=4)
    save_new_config_xray(xray_config_new)


add_client("bakvivas")












