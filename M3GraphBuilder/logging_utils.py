import logging

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"
)
encoding = "utf-8"


def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
