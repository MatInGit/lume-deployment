import colorlog, logging


def make_logger(name="model_manager", level=logging.DEBUG):

    logger = colorlog.getLogger(name)
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s[%(filename)s:%(lineno)s:%(funcName)s] %(levelname)s: %(message)s",
        datefmt=None,
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
    handler.setFormatter(formatter)

    # check if logger has handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(handler)

    logger.setLevel(logging.DEBUG)

    return logger


def get_logger():
    if not logging.getLogger().handlers:
        # If not, initialize a logger
        logger = logging.getLogger("model_manager")
        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter("%(log_color)s%(levelname)s:%(name)s:%(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)  # Set your desired log level here
        return logger
    else:
        # If a logger has already been initialized, use the existing one
        logger = logging.getLogger("model_manager")
        return logger
