import logging
import socket
import sys


# Обработчик для выхода при ошибках
class ErrorExitHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        if record.levelno >= logging.ERROR:
            sys.exit(1)


# Класс для логгера с контекстом
class ContextualLogger(logging.LoggerAdapter):
    def __init__(self, logger, local_hostname):
        super().__init__(logger, {})
        self.local_hostname = local_hostname

    def process(self, msg, kwargs):
        # Получаем удалённое имя хоста, если передано
        remote_hostname = kwargs.pop("remote_hostname", self.local_hostname)
        # Добавляем контекст локального и удалённого хоста
        if remote_hostname != self.local_hostname:
            return f"[{self.local_hostname} -> {remote_hostname}] {msg}", kwargs
        else:
            return f"{msg}", kwargs

# Основная конфигурация логгера
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    hostname = socket.gethostname()
    handler = ErrorExitHandler()

    # Формат логов
    formatter = logging.Formatter(f'{hostname} - %(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Инициализация обёртки для логгера
    context_logger = ContextualLogger(logger, hostname)

    return context_logger


# Получаем и экспортируем логгер
logger = setup_logger()
