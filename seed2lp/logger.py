import logging, logging.config
from logging import Logger
from os import path
from . import color, file
import yaml
from ._version import __version__

PROJECT_DIR = path.dirname(path.abspath(__file__))
#LOG_DIR:str
#log:logging.Logger
#verbose:bool

COLORS = {
    "WARNING": color.yellow,
    "INFO": color.grey,
    "DEBUG": color.reverse_colour,
    "CRITICAL": color.orange_back,
    "ERROR": color.red_bright,
    "RESET": color.reset
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, *, format:str, use_color:bool):
        logging.Formatter.__init__(self, fmt=format)
        self.use_color = use_color

    def format(self, record):
        msg = super().format(record)
        if self.use_color:
            levelname = record.levelname
            if hasattr(record, "color"):
                return f"{record.color}{msg}{COLORS['RESET']}"
            if levelname in COLORS:
                return f"{COLORS[levelname]}{msg}{COLORS['RESET']}"
        return msg
    


# def __init_logger_2__(log_path:str, verbose:bool=False):
#     """Init logger depending on log_path (and therefor run_mode)

#     Args:
#         log_path (str): Full path of logger file
#     """
#     global log
#     #logging.config.fileConfig(path.join(ROJECT_DIR,'log_conf.yaml'))
#     with open(path.join(ROJECT_DIR,'log_conf.yaml'), "rt") as f:
#         config = yaml.safe_load(f.read())
#         if verbose:
#             config['handlers']['console']['level']='DEBUG'
#         logging.config.dictConfig(config)
#     formatter = logging.Formatter('%(levelname)s %(asctime)s: %(message)s')
#     file_handler = logging.FileHandler(log_path)

#     if verbose:
#         file_handler.setLevel(logging.DEBUG)
#     else:
#         file_handler.setLevel(logging.INFO)
#     file_handler.setFormatter(formatter)

#     # create logger
#     log = logging.getLogger('s2lp')
#     log.addHandler(file_handler)


def init_logger(log_path: str, verbose: bool = False):
    """Init logger depending on log_path (and therefor run_mode). Return a logger
    needed for multiprocessing.

    Args:
        log_path (str): Full path of logger file
        verbose (bool, optional): Uses verbose mode. Defaults to False.

    Returns:
        logging.Logger: logger
    """
    logger = logging.getLogger("s2lp")

    if getattr(logger, "_configured", False):
        return logger

    # Console (YAML)
    with open(path.join(PROJECT_DIR, "log_conf.yaml"), "rt") as f:
        config = yaml.safe_load(f)
        if verbose:
            config["handlers"]["console"]["level"] = "DEBUG"
        logging.config.dictConfig(config)

    # Fichier (par process)
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    formatter = logging.Formatter(
        "%(levelname)s %(asctime)s [%(processName)s]: %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger._configured = True
    return logger


def print_log(logger: logging.Logger, message:str, level:str, col=None, verbose:bool=False):
    """Print and log messages

    Args:
        message (str): Message
        level (str): level of the message (info, error or debug)
    """
    if not verbose and level != "debug":
        if col:
            print(col + message + color.reset)
        else:
            print(message)
    else:
        pass

    match level:
        case "info":
            if col:
                logger.info(message,  extra={"color": col})
            else:
                logger.info(message)
        case "debug":
            logger.debug(message)
        case "warning":
            logger.warning(message)
        case "error":
            logger.error(message)



# def get_logger(sbml_file:str, short_option:str, verbose:bool=False) -> logging.Logger:
#     net_name = f'{path.splitext(path.basename(sbml_file))[0]}'
#     filename = f'{net_name}_{short_option}.log'
#     log_path = path.join(LOG_DIR, filename)
#     if file.existing_file(log_path):
#         file.delete(log_path)
#     logger=__init_logger__(log_path, verbose)
#     logger.info(f"Seed2LP version: {__version__}")
#     return logger

def get_logger(log_dir:str, sbml_file: str, short_option: str, verbose: bool = False):
    net_name = path.splitext(path.basename(sbml_file))[0]
    filename = f"{net_name}_{short_option}.log"
    log_path = path.join(log_dir, filename)

    if file.existing_file(log_path):
        file.delete(log_path)

    logger = init_logger(log_path, verbose)
    logger.info("Seed2LP version: %s", __version__)
    return logger, log_path


