import logging
import socket
import sys
import os


# Обработчик для выхода при ошибках
class ErrorExitHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        if record.levelno >= logging.ERROR:
            sys.exit(1)


# Класс для логгера с контекстом
class ContextualLogger(logging.LoggerAdapter):
    def __init__(self, logger, local_ip):
        super().__init__(logger, {})
        self.local_ip = local_ip

    def process(self, msg, kwargs):
        # Получаем название файла без пути
        current_file = os.path.basename(sys.argv[0])  # Извлекаем только имя файла
        current_function = "Unknown function"
        current_line = "Unknown line"

        # Если передан remote_ip, используем его, иначе только local_ip
        remote_ip = kwargs.pop("remote_ip", None)
        if remote_ip:
            return f"[{current_file}] [{self.local_ip} -> {remote_ip}] {msg}", kwargs
        else:
            return f"[{current_file}] [{self.local_ip}] {msg}", kwargs


# Функция для получения локального IP-адреса
def get_local_ip():
    try:
        # Определяем IP через подключение к внешнему ресурсу (на случай нескольких интерфейсов)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


# Основная конфигурация логгера
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    local_ip = get_local_ip()
    handler = ErrorExitHandler()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    context_logger = ContextualLogger(logger, local_ip)

    return context_logger


logger = setup_logger()
