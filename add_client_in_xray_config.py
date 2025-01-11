import json
import logging
import socket
import subprocess
import pathlib
import sys


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
def create_uuid_shotids(email):
    logging.info(f"I enter the command to get the uuid for user {email}")
    command_get_uuid = "/usr/local/bin/xray uuid"
    result_command_get_uuid = subprocess.run(command_get_uuid, shell=True, capture_output=True, text=True)

    stdout_result_command_get_uuid = result_command_get_uuid.stdout.strip()
    stderr_result_command_get_uuid = result_command_get_uuid.stderr.strip()
    exit_code_result_command_get_uuid = result_command_get_uuid.returncode

    if exit_code_result_command_get_uuid == 0:
        logging.info("uuid received successfully")
        logging.debug(f"uuid: \n{stdout_result_command_get_uuid}")
    else:
        logging.error(f"Error while getting uuid: \n"
                      f"{stderr_result_command_get_uuid}\n"
                      f"exit_code: {exit_code_result_command_get_uuid}")
    logging.info("uuid successfully generated")

    logging.info(f"I enter the command to get shorts id for user {email}")
    command_get_uuid = "openssl rand -hex 8"
    result_command_get_shortids = subprocess.run(command_get_uuid, shell=True, capture_output=True, text=True)

    stdout_result_command_get_shortids = result_command_get_shortids.stdout.strip()
    stderr_result_command_get_shortids = result_command_get_shortids.stderr.strip()
    exit_code_result_command_get_shortids = result_command_get_shortids.returncode

    if exit_code_result_command_get_shortids == 0:
        logging.info("Shorts id received successfully")
        logging.debug(f"Shorts id: \n{stdout_result_command_get_shortids}")
    else:
        logging.error(f"Error while getting shorts id: \n"
                      f"{stderr_result_command_get_shortids}\n"
                      f"exit_code: {exit_code_result_command_get_shortids}")
    logging.info("Shorts id successfully generated")


    return stdout_result_command_get_uuid, stdout_result_command_get_shortids


def get_old_config_inbounds():
    logging.info("Took xray inbounds config for processing")
    xray_config_inbounds_path = "/home/xray/confs/inbounds.json"
    try:
        with open(xray_config_inbounds_path, "r") as json_file:
            xray_config_inbounds_json = json.load(json_file)
    except PermissionError as e:
        logging.error(f"Insufficient permissions to read xray inbounds config: \n{e}")
    except Exception as e:
        logging.error(f"Error while trying to read xray inbounds config: \n{e}")

    logging.info("Xray inbounds config file read successfully")
    return xray_config_inbounds_json


def save_new_inbounds(path, new_inbounds):

    logging.debug(f"Начинаю сохранять inbounds с новым клиентом")
    try:
        with open(path, "w") as file:
            file.write(new_inbounds)
        logging.info(f"Inbounds с новым клинетом успешно сохранен")
    except Exception as e:
        logging.error(f"Ошибка при сохранении inbounds с новым клиентом: \n{e}")


def save_new_config_inbounds_xray(path, xray_config_inbounds_new):

    try:
        with open(path, "w") as file:
            file.write(xray_config_inbounds_new)
    except PermissionError as e:
        logging.error(f"Insufficient permissions to write to file: \n{e}")
    except Exception as e:
        logging.error(f"Unexpected error writing to file: \n{e}")
    logging.info("New user successfully added to xray config")


# Это общая функция для добавления пользователя в конфигурацию xray
def add_client(email):

    uuid, shortids = create_uuid_shotids(email)

    new_client = {
        "id": uuid,
        "flow": "xtls-rprx-vision"
    }

    xray_config_inbounds_old_json = get_old_config_inbounds()
    xray_config_inbounds_new_json = xray_config_inbounds_old_json
    xray_config_inbounds_new_json["inbounds"][0]["settings"]["clients"].append(new_client)
    xray_config_inbounds_new_json["inbounds"][0]["streamSettings"]["realitySettings"]["shortIds"].append(shortids)

    xray_config_inbounds_new = json.dumps(xray_config_inbounds_new_json, sort_keys=True, indent=4)
    path = "/home/xray/confs/inbounds.json"
    save_new_config_inbounds_xray(path, xray_config_inbounds_new)

    return uuid, shortids

# add_client("bakvivas")












