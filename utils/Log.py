#!/usr/bin/env python
# encoding: utf-8

import logging
from colorlog import ColoredFormatter

FORMAT = "%(asctime)s %(levelname)s %(module)s-%(lineno)d %(message)s"
COLOR_FORMAT = "%(asctime)s %(log_color)s%(levelname)s %(module)s-%(lineno)d %(message)s%(reset)s"


def get_level(level):
    if isinstance(level, str)is False:
        return level

    level = level.lower()

    if level == "warn" or level == "warning":
        return logging.WARN
    elif level == "error":
        return logging.ERROR
    elif level == "info":
        return logging.INFO
    elif level == "debug":
        return logging.DEBUG
    else:
        return logging.DEBUG


def get_logger(name):
    _log = logging.getLogger(name)
    _log.setLevel(logging.DEBUG)

    if not _log.handlers:
        _stream = logging.StreamHandler()
        _stream.setFormatter(ColoredFormatter(COLOR_FORMAT))
        _log.addHandler(_stream)

    _log.set_level = lambda level: _log.handlers[0].setLevel(get_level(level))
    _log.set_level("info")

    def _add_file(file, level):
        level = get_level(level)
        handler = logging.FileHandler(file, mode='a', encoding='utf8', delay=False)
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(FORMAT))
        _log.addHandler(handler)

    _log.add_file = lambda file, level = "debug": _add_file(file, level)
    return _log

log = get_logger(__name__)
