# Включаем GUI в браузере для удобной работы
ui = true

# Адресс для API
api_addr = "https://127.0.0.1:8200"

cluster_addr = "https://127.0.0.1:8201"
cluster_name = "vault-cluster"

# Отключаем предупреждение mlock, потом все настроить правильно
disable_mlock = true



# Настройка слушателя для TCP
listener "tcp" {
  address     = "0.0.0.0:8200" 
  tls_cert_file = "/etc/ssl/certs/vault-cert.pem"
  tls_key_file = "/etc/ssl/certs/vault-key.pem"
}

# Настройка хранилища 
backend "raft" {
  path = "/home/bakvivas/vault"
  node_id = "vault-server"
}