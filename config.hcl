# Включаем GUI в браузере для удобной работы
ui = true

# Отключаем предупреждение mlock, потом все настроить правильно
disable_mlock = true

# Настройка слушателя для TCP
listener "tcp" {
  address     = "0.0.0.0:8200" 
  tls_disable = true
}

# Настройка хранилища 
storage "file" {
  path = "/home/bakvivas/vault_disk"
}