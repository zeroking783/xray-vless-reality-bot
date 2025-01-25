from fastapi inport FastAPI, HTTPException
import grpc
import xray_pb2
import xray_pb2_grpc
import vault_func 
import db_func
import redis

def initialize_resources():
    vault_token = get_vault_token()
    client = create_vault_client("https://127.0.0.1:8200", vault_token, "/etc/ssl/certs/vault-cert.pem")

    data_db_connect = read_secret_vault(client, 'Cloak/databases/settings_server_db')
    conn, cursor = connect_to_db(data_db_connect["db_host"], 
                            data_db_connect["db_port"], 
                            data_db_connect["db_name"], 
                            data_db_connect["db_user"], 
                            data_db_connect["user_password"])

    data_db_connect = read_secret_vault(client, 'Cloak/databases/redis')
    r = redis.Redis(host=data_db_connect["db_host"], port=data_db_connect["port"], decode_responses=True)

    return conn, cursor, r

def create_tls(server_id):
    

def check_tls(server_id, conn, cursor, r):
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
            create_tls(server_id)
            return True

def send_request(conn, cursor, r, ip):
    with grpc.insecure_channel('138.124.31.142:50051') as channel:
        stub = xray_pb2_grpc.XrayClientsServiceStub(channel)  # Используем сгенерированный клиент
        # Отправка запроса AddClient
        response = stub.AddClient(xray_pb2.ClientIdRequest(name="bakvivas"))
        print(f"Received response: UUID={response.uuid}, Short ID={response.shortids}")

@app.on_event("startup")
async def startup_event():
    global conn, cursor, r
    conn, cursor, r = initialize_resources()

@app.on_event("shutdown")
async def shutdown_event():
    cursor.close()
    conn.close()
    r.close()

@app.post("/create_client")
async def create_client(server_id: str, client_id: str):
    try:
        result = await send_grpc_request(server_id, name, conn, cursor, r)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
