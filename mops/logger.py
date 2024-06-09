import logging
from pathlib import Path

import colorlog


def get_logger(path: Path):
    logger = logging.getLogger(path.as_posix())
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(logging.INFO)

        console_handler = colorlog.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%m-%d %H:%M:%S"
        )
        color_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)-8s%(reset)s %(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
            datefmt="%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(color_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
