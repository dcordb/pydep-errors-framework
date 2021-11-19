import logging


def stream_logger(name: str, level: int = logging.DEBUG):
    logger = logging.getLogger(name)
    configure_logger(logger, level)
    return logger


def configure_logger(logger, level: int = logging.DEBUG):
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(fmt="{levelname} ({module}:{lineno}): {message}", style="{")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
