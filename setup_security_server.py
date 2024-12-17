import random
from ssh_client import create_ssh_connection, closed_ssh_connection
from base_function import change_string_in_file
from base_function import restart_service
from base_function import generate_password
from base_function import create_user
from base_function import get_free_name_server
from base_function import write_data_in_file


# Создаю соединение по ssh с сервером
ssh_client = create_ssh_connection(ip="138.124.31.142", username="root", password="5yOs3Wc5Poc070", port="22")

# Меняю название сервера
new_server_name = get_free_name_server()
write_data_in_file("/etc/hostname", new_server_name, recreate=True, ssh_client=ssh_client)

# Изменяю порт на какой-то повыше
port_number = random.randint(20000, 65000)
port_string = "Port=" + str(port_number)
print(port_string)
change_string_in_file("/etc/ssh/sshd_config", r"^#?Port\s+\d+", port_string, ssh_client=ssh_client)

# Добавляю нового пользователя на сервер
password = generate_password()
print(password)
create_user(password, "xray-worker", ssh_client=ssh_client)

# Отключаем подключение к root по ssh
change_string_in_file("/etc/ssh/sshd_config", r"^PermitRootLogin\s+(yes|no)", "PermitRootLogin no", ssh_client=ssh_client)

# Перезагружаю ssh службу
restart_service("ssh", ssh_client=ssh_client)

# Настраиваю ssh ключи


closed_ssh_connection(ssh_client)




