import sys
import requests
import json
import os


try:
    role_id = os.getenv("role_id")
    secret_id = os.getenv("secret_id")
    vault_addr = os.getenv("VAULT_ADDR")
except Exception as e:
    print(f"Ошибка при чтении переменных окружения: {e}", file=sys.stderr)
    sys.exit(1)


url = f"{vault_addr}/v1/auth/approle/login"
data = {
    "role_id": role_id,
    "secret_id": secret_id
}

try:
    response = requests.post(url, json=data, verify=False)
except Exception as e:
    print(f"Ошибка при отправке https запроса для получения токена: {e}", file=sys.stderr)
    sys.exit(2)


if response.status_code == 200:
    try:
        data = response.json()
    except Exception as e:
        print(f"Ошибка при сохранении файла в формате json: {e}", file=sys.stderr)
        sys.exit(3)
    
    try:
        print(data["auth"]["client_token"])
        print(data["auth"]["accessor"])
    except Exception as e:
        print(f"Ошибка при извлечении из ответа client_token и accessor_token: {e}", file=sys.stderr)
        sys.exit(4)
else:
    sys.exit(f"Не удалось отправить запрос по этому url: {response.stat}")