import logging


def stream_logger(name: str, level: int = logging.DEBUG):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(fmt="{levelname} ({module}:{lineno}): {message}", style="{")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
