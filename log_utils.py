import logging


def get_basic_logger(name, sev_str='i'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create console handler and set level
    ch = logging.StreamHandler()
    if sev_str == 'd':
        sev = logging.DEBUG
    elif sev_str == 'w':
        sev = logging.WARN
    elif sev_str == 'e':
        sev = logging.ERROR
    elif sev_str == 'c':
        sev = logging.CRITICAL
    elif sev_str == 'i':
        sev = logging.INFO  # default to info behavior.
    else:
        raise ValueError(f"get_basic_logger received invalid severity '{sev_str}'")
    ch.setLevel(sev)
    # create formatter
    formatter = logging.Formatter(
        '[%(levelname)s][%(asctime)s][%(name)s] %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    return logger
