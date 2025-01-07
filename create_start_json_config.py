import os
import subprocess
import logging
import sys
import socket
import json
import pathlib


# Logger configuration
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


# We get private and public keys
def get_key():
    logging.info("I enter the command to get the keys")
    command_get_key = "/usr/local/bin/xray x25519"
    result_command_get_key = subprocess.run(command_get_key, shell=True, capture_output=True, text=True)

    stdout_result_command_get_key = result_command_get_key.stdout
    stderr_result_command_get_key = result_command_get_key.stderr
    exit_code_result_command_get_key = result_command_get_key.returncode

    if exit_code_result_command_get_key == 0:
        logging.info("Keys received successfully")
        logging.debug(f"keys: \n{stdout_result_command_get_key}")
    else:
        logging.error(f"Error while getting keys: \n"
                      f"{stderr_result_command_get_key}\n"
                      f"exit_code: {exit_code_result_command_get_key}")

    key_text_to_lines = stdout_result_command_get_key.strip().split("\n")

    private_key = key_text_to_lines[0].split(":")[1].strip()
    public_key = key_text_to_lines[1].split(":")[1].strip()

    logging.info("privateKey and publicKey successfully generated")

    return private_key, public_key


# Get shorIds
def get_shortids():
    logging.info("I enter the command to get ShortIds")
    command_get_shortids = "openssl rand -hex 8"
    result_command_get_shortids = subprocess.run(command_get_shortids, shell=True, capture_output=True, text=True)

    stdout_result_command_get_shortids = result_command_get_shortids.stdout
    stderr_result_command_get_shortids = result_command_get_shortids.stderr
    exit_code_result_command_get_shortids = result_command_get_shortids.returncode

    if exit_code_result_command_get_shortids == 0:
        logging.info("ShortIds received successfully")
        logging.debug(f"shortIds: \n{stdout_result_command_get_shortids}")
    else:
        logging.error("Error getting shortIds: \n"
                      f"{stderr_result_command_get_shortids}"
                      f"exit_code: {exit_code_result_command_get_shortids}\n")

    return stdout_result_command_get_shortids


# Configuring basic json
def configure_xray_config(private_key, public_key, short_ids, path_file):
    try:
        logging.debug(f"Открываю конфигурационный json файл {path_file}")
        with open(path_file, 'r') as file:
            data = json.load(file)
        logging.info(f"Конфигурационный json файл {path_file} открыт")
    except Exception as e:
        logging.error(f"Не удалось открыть файл {path_file} конфигурации xray")

    logging.info(f"Начинаю изменять данные в файле конфигурации xray {path_file}")
    try:
        logging.debug(f"Изменяю данные в конфигурационном файле {path_file}")
        data["inbounds"][0]["streamSettings"]["realitySettings"]["privateKey"] = private_key
        data["inbounds"][0]["streamSettings"]["realitySettings"]["publicKey"] = public_key
        data["inbounds"][0]["streamSettings"]["realitySettings"]["shortIds"] = [short_ids.strip()]
        logging.info(f"Конфигурационные данные в файле json {path_file} успешно изменены")
    except Exception as e:
        logging.error(f"Не удалось изменить данные в json {path_file}")

    try:
        logging.debug(f"Начинаю сохранять измененный {path_file}")
        with open(path_file, 'w') as file:
            json.dump(data, file, indent=4)
        logging.info(f"Измененный {path_file} успешно сохранен")
    except Exception as e:
        logging.error(f"Не удалось сохранить измененный {path_file}")


def get_xray_config_version(path_file):
    try:
        logging.debug(f"Открываю json файл {path_file} с версией конфига")
        with open(path_file, 'r') as file:
            data = json.load(file)
        logging.info(f"Json файл {path_file} с версией конфига открыт")
    except Exception as e:
        logging.error(f"Не удалось открыть файл {path_file} с версией конфигурации xray")

    try:
        logging.debug(f"Считываю версию конфига xray {path_file}")
        version = data.get("version")
        logging.info(f"Версия конфига {path_file} считана")
    except Exception as e:
        logging.error(f"Не удалось считать версию конфига xray {path_file}")

    return version

private_key, public_key = get_key()
short_ids = get_shortids()
configure_xray_config(private_key, public_key, short_ids, "/home/xray/confs/inbounds.json")

version_xray_config = get_xray_config_version("/home/xray/confs/version.json")
print(version_xray_config)
os.environ["XRAY_CONFIG"] = version_xray_config
os.system[f"export XRAY_CONFIG={version_xray_config}"]