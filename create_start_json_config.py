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


private_key, public_key = get_key()
short_ids = get_shortids()
xray_config_base_json = create_start_xray_config(private_key, public_key, short_ids)
save_information_in_file("/usr/local/etc/xray", "config.json", xray_config_base_json, True)







