from logger import logger
import argparse
import paramiko

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
    ip, username, password, port, key_path = parse_arguments_for_ssh()

    ssh_client = paramiko.SSHClient()
