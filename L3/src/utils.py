from app import app
import sys


def create_tls(server_id, ip):
    certificate_response = app.state.vault_client.write(
        f"pki_int/issue/ip-role",
        common_name="localhost",
        ip_sans=ip,
        ttl="72h"
    )
    if not certificate_response:
        sys.exit(f"Не удалось создать сертификат в Vault")
    crt = certificate_response['data']['certificate']
    key = certificate_response['data']['private_key']

    with open(f"L3/servers_certificates/{server_id}.crt", "w") as f:
        f.write(crt)
    with open(f"L3/servers_certificates/{server_id}.key", "w") as f:
        f.write(key)

    send_certificate(ip, server_id)



def check_tls(server_id, ip):
    server_id = server_id.split('-')[-1]
    redis_responce = app.state.redis.get(server_id)

    if redis_responce is not None:
        return True
    else:
        postgre_request = """
            SELECT tls_certificate FROM servers.initial WHERE id = %s;
        """
        app.state.cursor.execute(postgre_request, (server_id, ))
        postgre_responce = app.state.cursor.fetchone()

        if postgre_responce:
            app.state.redis.set(server_id, '1')
            return True
        else:
            create_tls(server_id, ip)
            return True


def read_cert(server_id):
    try:
        with open(f"L3/servers_certificates/{server_id}.crt", "r") as f:
            cert = f.read()
            return cert
    except Exception as e:
        sys.exit(f"Ошибка при чтении сертификата: {e}")

def read_key(server_id):
    try:
        with open(f"L3/servers_certificates/{server_id}.key", "r") as f:
            key = f.read()
            return key
    except Exception as e:
        sys.exit(f"Ошибка при чтении приватного ключа сертификата: {e}")