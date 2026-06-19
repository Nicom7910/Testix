import logging
from logging.handlers import RotatingFileHandler
import os


LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "sistema.log")


def configurar_logger():
    """
    Configura el logger principal del sistema.

    El sistema guarda los eventos importantes en logs/sistema.log.
    Se utiliza RotatingFileHandler para evitar que el archivo crezca indefinidamente.
    """

    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("testix")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    archivo_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    archivo_handler.setLevel(logging.INFO)
    archivo_handler.setFormatter(formato)

    consola_handler = logging.StreamHandler()
    consola_handler.setLevel(logging.INFO)
    consola_handler.setFormatter(formato)

    logger.addHandler(archivo_handler)
    logger.addHandler(consola_handler)

    return logger


logger = configurar_logger()