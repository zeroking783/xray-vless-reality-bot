import subprocess
import logging
import sys
import socket
import json
import pathlib


### НАСТРОЙКА ЛОГЕРА ###
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


### Получаем приватный и публичный ключи
def get_key():
    logging.info("Ввожу команду для получения ключей")
    command_get_key = "/usr/local/bin/xray x25519"
    result_command_get_key = subprocess.run(command_get_key, shell=True, capture_output=True, text=True)

    stdout_result_command_get_key = result_command_get_key.stdout
    stderr_result_command_get_key = result_command_get_key.stderr
    exit_code_result_command_get_key = result_command_get_key.returncode

    if exit_code_result_command_get_key == 0:
        logging.info("Ключи получены успешно")
        logging.debug(f"keys: \n{stdout_result_command_get_key}")
    else:
        logging.error(f"Ошибка при получении ключей: \n"
                      f"{stderr_result_command_get_key}\n"
                      f"exit_code: {exit_code_result_command_get_key}")

    key_text_to_lines = stdout_result_command_get_key.strip().split("\n")

    private_key = key_text_to_lines[0].split(":")[1].strip()
    public_key = key_text_to_lines[1].split(":")[1].strip()

    return private_key, public_key


# Получаю shorIds
def get_shortids():
    logging.info("Ввожу команду для получения ShortIds")
    command_get_shortids = "openssl rand -hex 8"
    result_command_get_shortids = subprocess.run(command_get_shortids, shell=True, capture_output=True, text=True)

    stdout_result_command_get_shortids = result_command_get_shortids.stdout
    stderr_result_command_get_shortids = result_command_get_shortids.stderr
    exit_code_result_command_get_shortids = result_command_get_shortids.returncode

    if exit_code_result_command_get_shortids == 0:
        logging.info("ShortIds получен успешно")
        logging.debug(f"shortIds: \n{stdout_result_command_get_shortids}")
    else:
        logging.error("Ошибка при получении shortIds: \n"
                      f"{stderr_result_command_get_shortids}"
                      f"exit_code: {exit_code_result_command_get_shortids}\n")

    return stdout_result_command_get_shortids


# Конфигурирую базовый json
def create_start_config(private_key, public_key, short_ids):

    config_base = {
        "log": {"loglevel": "info"},
        "routing": {"rules": [],
                    "domainStrategy": "AsIs"},
        "inbounds": [{"port": 443,
                      "protocol": "vless",
                      "tag": "vless_tls",
                      "settings": {},
                      "streamSettings": {
                          "network": "tcp",
                          "security": "reality",
                          "realitySettings": {
                              "show": False,
                              "dest": "www.yahoo.com:443",
                              "xver": 0,
                              "serverNames": ["www.yahoo.com"],
                              "privateKey": private_key,
                              "publicKey": public_key,
                              "minClientVer": "",
                              "maxClientVer": "",
                              "maxTimeDiff": 0,
                              "shortIds": [short_ids]}
                              },
                          "sniffing": {
                              "enabled": True,
                              "destOverride": ["http", "tls"]
                          }
                      }
                     ],
        "outbounds": [
            {"protocol": "freedom",
             "tag": "direct"},
            {"protocol": "blackhole",
             "tag": "block"}
        ]
    }

    try:
        config_base_json = json.dumps(config_base, sort_keys=True, indent=4)
    except Exception as e:
        logging.error(f"Не удалось собрать начальную конфигурацию xray: \n{e}")

    logging.info("Начальная конфигурация xray успешно собрана в json")

    return config_base_json


def save_start_config(config_base_json):

    save_directory = "/usr/local/etc/xray"
    config_path = pathlib.Path(save_directory) / "config.json"

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        logging.error(f"Недостаточно прав для создания директории: \n{e}")
    except Exception as e:
        logging.error(f"Неожиданая ошибка при создании директории: \n{e}")
    logging.info("Директория /usr/local/etc/xray присутствует/создана")

    try:
        with open(config_path, "w") as file:
            file.write(config_base_json)
    except PermissionError as e:
        logging.error(f"Недостаточно прав для записи в файл: \n{e}")
    except Exception as e:
        logging.error(f"Неожиданная ошибка при записи в файл: \n{e}")
    logging.info("config_base_json успешно записался в /usr/local/etc/xray/config.json")



private_key, public_key = get_key()
short_ids = get_shortids()
config_base_json = create_start_config(private_key, public_key, short_ids)
save_start_config(config_base_json)







