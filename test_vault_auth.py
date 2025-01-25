import os
import hvac

# Получение токена из переменной окружения
vault_token = os.getenv('VAULT_TOKEN')
if not vault_token:
    raise Exception("VAULT_TOKEN переменная окружения не установлена")

# Создание клиента для Vault
client = hvac.Client(url='https://127.0.0.1:8200', 
                    token=vault_token,
                    verify='/etc/ssl/certs/vault-cert.pem')

# Проверка аутентификации
if client.is_authenticated():
    print("Аутентификация прошла успешно")

    read_response = client.secrets.kv.read_secret_version(path='Cloak/databases/settings_server_db')
    print(f"Вот твое значение: {read_response['data']['data']}")


else:
    print("Ошибка аутентификации")
