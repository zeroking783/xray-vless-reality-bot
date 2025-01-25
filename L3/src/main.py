from fastapi import FastAPI, HTTPException
import redis

import vault 
import databases
import grpc_client



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

@app.on_event("startup")
async def startup_event():
    conn, cursor, r, vault_client = initialize_resources()
    app.state.db_conn = conn
    app.state.cursor = cursor
    app.state.redis = r
    app.state.vault_client = vault_client

@app.on_event("shutdown")
async def shutdown_event():
    app.state.db_conn.close()
    app.state.cursor.close()
    app.state.redis.close()

@app.post("/create_client")
async def create_client(server_id: str, client_id: str, ip: str):
    server_id = server_id.split('-')[-1]
    try:
        result = await send_grpc_request(server_id, ip, "AddClient", client_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/delete_client")
