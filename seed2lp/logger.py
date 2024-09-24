import logging, logging.config
from os import path
from . import color, file
import yaml
from ._version import __version__

ROJECT_DIR = path.dirname(path.abspath(__file__))
LOG_DIR:str
log:logging.Logger
verbose:bool

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
    


def __init_logger__(log_path:str):
    """_summary_

    Args:
        log_path (str): _description_
        debug (bool): _description_

    Returns:
        _type_: _description_
    """
    global log
    #logging.config.fileConfig(path.join(ROJECT_DIR,'log_conf.yaml'))
    with open(path.join(ROJECT_DIR,'log_conf.yaml'), "rt") as f:
        config = yaml.safe_load(f.read())
        if verbose:
            config['handlers']['console']['level']='DEBUG'
        logging.config.dictConfig(config)
    formatter = logging.Formatter('%(levelname)s %(asctime)s: %(message)s')
    file_handler = logging.FileHandler(log_path)

    if verbose:
        file_handler.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # create logger
    log = logging.getLogger('s2lp')
    log.addHandler(file_handler)


def print_log(message:str, level:str, col=None):
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
                log.info(message,  extra={"color": col})
            else:
                log.info(message)
        case "debug":
            log.debug(message)
        case "warning":
            log.warning(message)
        case "error":
            log.error(message)



def get_logger(sbml_file:str, short_option:str, debug:bool=False):
    global log
    global verbose
    verbose=debug
    net_name = f'{path.splitext(path.basename(sbml_file))[0]}'
    filename = f'{net_name}_{short_option}.log'
    log_path = path.join(LOG_DIR, filename)
    if file.existing_file(log_path):
        file.delete(log_path)
    __init_logger__(log_path)
    log.info(f"Seed2LP version: {__version__}")


def set_log_dir(value):
    global LOG_DIR
    LOG_DIR = value
    