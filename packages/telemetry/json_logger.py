import logging


def get_logger(name="kyros"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        f = logging.Formatter(
            '{"level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
        )
        h.setFormatter(f)
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger
