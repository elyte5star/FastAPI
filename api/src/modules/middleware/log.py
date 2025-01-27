import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from os import path
from pathlib import Path
from psutil import cpu_percent, virtual_memory

base_dir = Path(__file__).parent.parent.parent.parent.parent
logs_target = path.join(base_dir / "logs", "api.log")
logs_error_target = path.join(base_dir / "logs", "error.log")


class UserFilter(logging.Filter):
    def filter(self, record) -> bool:
        record.user = "API"
        record.psutil = f"c{cpu_percent():02.0f}m{virtual_memory().percent:02.0f}"
        return True


FORMATTER = logging.Formatter(
    "%(levelname)s::%(psutil)s::%(asctime)s :: %(name)s :: %(funcName)s :: %(message)s"
)


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(filename: str):
    file_handler = TimedRotatingFileHandler(filename, when="midnight")
    file_handler.setFormatter(FORMATTER)
    return file_handler


def log_config(console_log_level: str = "DEBUG") -> dict:

    LOGGING_CONFIG = {
        "version": 1,
        "filters": {"psutil": {"()": "modules.middleware.log.UserFilter"}},
        "formatters": {
            "json": {
                "format": "%(levelname)s :: %(asctime)s :: %(name)s :: %(funcName)s :: %(message)s",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            },
            "error": {
                "format": "%(levelname)s :: %(asctime)s :: %(name)s :: %(funcName)s :: %(message)s",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            },
            "standard": {
                "format": "%(levelname)s :: %(asctime)s :: %(name)s :: %(funcName)s :: %(message)s"
            },
        },
        "handlers": {
            "console": {
                "level": console_log_level,
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": sys.stdout,
                "filters": ["psutil"],
            },
            "info_rotating_file_handler": {
                "level": "INFO",
                "formatter": "json",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logs_target,
                "mode": "a",
                "maxBytes": 1048576,
                "backupCount": 10,
                "encoding": "utf8",
            },
            "error_file_handler": {
                "level": "WARNING",
                "formatter": "error",
                "class": "logging.FileHandler",
                "filename": logs_error_target,
                "mode": "a",
            },
            "critical_mail_handler": {
                "level": "CRITICAL",
                "formatter": "error",
                "class": "logging.handlers.SMTPHandler",
                "mailhost": "localhost",
                "fromaddr": "monitoring@domain.com",
                "toaddrs": ["dev@domain.com", "qa@domain.com"],
                "subject": "Critical error with application name",
            },
        },
        "root": {
            "level": "NOTSET",
            "handlers": [
                "console",
                "info_rotating_file_handler",
                "error_file_handler",
                "critical_mail_handler",
            ],
        },
    }
    return LOGGING_CONFIG
