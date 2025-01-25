from fastapi import FastAPI, HTTPException
import grpc
import xray_pb2
import xray_pb2_grpc
import vault_func 
import db_func
import redis

def initialize_resources():
    vault_token = get_vault_token()
    vault_client = create_vault_client("https://127.0.0.1:8200", vault_token, "/etc/ssl/certs/vault-cert.pem")

    data_db_connect = read_secret_vault(vault_client, 'Cloak/databases/settings_server_db')
    conn, cursor = connect_to_db(data_db_connect["db_host"], 
                            data_db_connect["db_port"], 
                            data_db_connect["db_name"], 
                            data_db_connect["db_user"], 
                            data_db_connect["user_password"])

    data_db_connect = read_secret_vault(vault_client, 'Cloak/databases/redis')
    r = redis.Redis(host=data_db_connect["db_host"], port=data_db_connect["port"], decode_responses=True)

    return conn, cursor, r, vault_client


def create_tls(server_id, vault_client, ip):
    certificate_response = vault_client.write(
        f"pki_int/issue/ip-role",
        common_name="localhost",
        ip_sans=ip,
        ttl="72h"
    )
    if not certificate_response:
        sys.exit(f"Не удалось создать сертификат в Vault")
    crt = certificate_response['data']['certificate']
    key = certificate_response['data']['private_key']

    with open(f"servers_certificates/{ip}.crt") as f:
        f.write(crt)
    with open(f"servers_certificates/{ip}.key") as f:
        f.write(key)
    

def check_tls(server_id, conn, cursor, r, vault_client, ip):
    server_id = server_id.split('-')[-1]
    redis_responce = r.get(server_id)
    if redis_responce is not None:
        return True
    else:
        postgre_request = """
            SELECT tls_certificate FROM servers.initial WHERE id = %s;
        """
        cursor.execute(postgre_request, (server_id, ))
        postgre_responce = cursor.fetchone()
        if postgre_responce:
            r.set(server_id, '1')
            return True
        else:
            create_tls(server_id, vault_client, ip)
            return True

def send_grpc_request(server_id, ip, client_id, conn, cursor, r, vault_client):
    if not check_tls(server_id, conn, cursor, r, vault_client, ip):
        sys.exit(f"Не удалось проверить сертификат или не удалось создать его")
    
    with open(f"servers_certificates/{ip}.crt", "r") as f:
        certificate = f.read()
    with open(f"servers_certificates/{ip}.key", "r") as f:
        private_key = f.read()
    
    credentials = grpc.ssl_channel_credentials(
        certificate_chain=certificate.encode(),
        private_key=private_key.encode()
    )

    with grpc.secure_channel(f"{ip}:50051", credentials) as channel:
        stub = xray_pb2_grpc.XrayClientsServiceStub(channel)  # Используем сгенерированный клиент
        # Отправка запроса AddClient
        response = stub.AddClient(xray_pb2.ClientIdRequest(name=client_id))
        print(f"Received response: UUID={response.uuid}, Short ID={response.shortids}")

@app.on_event("startup")
async def startup_event():
    global conn, cursor, r, vault_client
    conn, cursor, r, vault_client = initialize_resources()

@app.on_event("shutdown")
async def shutdown_event():
    cursor.close()
    conn.close()
    r.close()

@app.post("/create_client")
async def create_client(server_id: str, client_id: str, ip: str):
    server_id = server_id.split('-')[-1]
    try:
        result = await send_grpc_request(server_id, ip, client_id, conn, cursor, r, vault_client)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
