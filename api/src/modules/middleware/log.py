import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from os import path, getenv
from pathlib import Path
from psutil import cpu_percent, virtual_memory
from pythonjsonlogger import jsonlogger


base_dir = Path(__file__).parent.parent.parent.parent.parent
logs_target = path.join(base_dir / "logs", "api.log")
logs_error_target = path.join(base_dir / "logs", "error.log")


fmt = "%(levelname)s::%(psutil)s::%(asctime)s :: %(name)s :: %(funcName)s :: Run by: %(current_user)s :: %(message)s"


class UserFilter(logging.Filter):
    def filter(self, record) -> bool:
        record.current_user = str(getenv("current_user", "API"))
        record.psutil = f"c{cpu_percent():02.0f}m{virtual_memory().percent:02.0f}"
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(
            log_record,
            record,
            message_dict,
        )
        if not log_record.get("current_user"):
            log_record["current_user"] = "API"
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


FORMATTER = logging.Formatter(
    fmt,
    defaults={
        "current_user": "API",
    },
)


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    console_handler.addFilter(UserFilter())
    return console_handler


def get_file_handler(filename: str = logs_target):
    file_handler = TimedRotatingFileHandler(filename, when="midnight")
    formatter = CustomJsonFormatter(fmt)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(UserFilter())
    return file_handler


def log_config(console_log_level: str = "DEBUG") -> dict:

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": True,
        "filters": {"psutil": {"()": "modules.middleware.log.UserFilter"}},
        "formatters": {
            "json": {
                "format": fmt,
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            },
            "error": {
                "format": fmt,
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            },
            "standard": {"format": fmt},
        },
        "handlers": {
            "console": {
                "level": console_log_level,
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
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
            },
            "error_file_handler": {
                "level": "WARNING",
                "formatter": "error",
                "class": "logging.FileHandler",
                "filename": logs_error_target,
                "mode": "a",
                "filters": ["psutil"],
            },
            "critical_mail_handler": {
                "level": "CRITICAL",
                "formatter": "error",
                "class": "logging.handlers.SMTPHandler",
                "mailhost": "localhost",
                "fromaddr": "monitoring@domain.com",
                "toaddrs": ["dev@domain.com", "qa@domain.com"],
                "subject": "Critical error with application name",
                "filters": ["psutil"],
            },
        },
        "loggers": {
            "": {
                "level": console_log_level,
                "handlers": ["console"],
            },
            "__main__": {  # if __name__ == '__main__'
                "handlers": ["console"],
                "level": console_log_level,
                "propagate": False,
            },
            "src.modules": {
                "level": "WARNING",
                "propagate": False,
                "handlers": [
                    "info_rotating_file_handler",
                    "error_file_handler",
                    "console",
                ],
            },
        },
    }
    return LOGGING_CONFIG
