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
def create_start_xray_config(private_key, public_key, short_ids):

    xray_config_base = {
        "log": {"loglevel": "info"},
        "routing": {"rules": [],
                    "domainStrategy": "AsIs"},
        "inbounds": [{"port": 443,
                      "protocol": "vless",
                      "tag": "vless_tls",
                      "settings": {
                          "clients": [],
                          "decryption": "none"
                      },
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
        xray_config_base_json = json.dumps(xray_config_base, sort_keys=True, indent=4)
    except Exception as e:
        logging.error(f"Failed to build initial xray configuration: \n{e}")

    logging.info("Initial xray configuration successfully compiled into json")

    return xray_config_base_json


# I save the initial xray configuration in /usr/local/etc/xray/config.json
def save_start_config(xray_config_base_json):

    save_directory = "/usr/local/etc/xray"
    xray_config_path = pathlib.Path(save_directory) / "config.json"

    try:
        xray_config_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        logging.error(f"Insufficient permissions to create directory: \n{e}")
    except Exception as e:
        logging.error(f"Unexpected error creating directory: \n{e}")
    logging.info("Directory /usr/local/etc/xray is present/created")

    try:
        with open(xray_config_path, "w") as file:
            file.write(xray_config_base_json)
    except PermissionError as e:
        logging.error(f"Insufficient permissions to write to file: \n{e}")
    except Exception as e:
        logging.error(f"Unexpected error writing to file: \n{e}")
    logging.info("config_base_json successfully written to /usr/local/etc/xray/config.json")


private_key, public_key = get_key()
short_ids = get_shortids()
xray_config_base_json = create_start_xray_config(private_key, public_key, short_ids)
save_start_config(xray_config_base_json)







