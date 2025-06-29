import logging
import sys
from logging.handlers import (
    TimedRotatingFileHandler,
    SMTPHandler,
    QueueHandler,
)
from os import path, getenv
from pathlib import Path
from modules.settings.configuration import ApiConfig
from modules.utils.misc import get_indent, date_time_now_utc
import json
from multiprocessing import Queue

base_dir = Path(__file__).parent.parent.parent.parent.parent
logs_target = path.join(base_dir / "logs", "api.log")
logs_error_target = path.join(base_dir / "logs", "error.log")


fmt = "%(levelname)s::%(asctime)s::%(name)s::%(funcName)s:%(module)s:currentUser:%(currentUser)s::logId:%(logId)s::%(message)s"


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
            "time": self.formatTime(record, self.datefmt),
            "function": record.funcName,
            "currentUser": str(getenv("current_user", "API")),
            "logId": get_indent(),
            "filename": record.filename,
            "module": record.module,
            "filePathName": record.pathname,
        }
        return json.dumps(log_record, sort_keys=False)


class QueueLoggingHandler(QueueHandler):
    def __init__(self, queue: Queue) -> None:
        super().__init__(queue)

    def emit(self, record: logging.LogRecord) -> None:
        return super().emit(record)

    def close(self) -> None:
        return super().close()


class UserFilter(logging.Filter):
    def filter(self, record) -> bool:
        record.currentUser = str(getenv("current_user", "API"))
        record.logId = get_indent()
        return True


FORMATTER = logging.Formatter(fmt)

FORMATTER.converter = lambda *args: date_time_now_utc().timetuple()


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    console_handler.addFilter(UserFilter())
    return console_handler


def smtp_log_handler(cfg: ApiConfig):
    smtp_handler = SMTPHandler(
        mailhost=(cfg.mail_server, cfg.mail_port),
        fromaddr=cfg.email,
        toaddrs=["elyte5star@gmail.com"],
        subject="Exceptional Log",
        credentials=(cfg.mail_username, cfg.mail_password),
        secure=None,
    )
    smtp_handler.setFormatter(JSONFormatter())
    smtp_handler.setLevel(logging.CRITICAL)
    return smtp_handler


def info_file_handler(filename: str = logs_target):
    file_handler = TimedRotatingFileHandler(filename, when="midnight")
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(logging.INFO)
    return file_handler


def error_file_handler(filename: str = logs_error_target):
    file_handler = TimedRotatingFileHandler(filename, when="midnight")
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(logging.WARNING)
    return file_handler


# class CustomJsonFormatter(JsonFormatter):
#     def add_fields(self, log_record, record, message_dict) -> None:
#         super(CustomJsonFormatter, self).add_fields(Add commentMore actions
#             log_record,
#             record,
#             message_dict,
#         )
#         # Add fields here
#         log_record["asctime"] = date_time_now_utc().strftime("%d-%m-%Y, %H:%M:%S.%f")

# def log_config(console_log_level: str = "DEBUG") -> dict:

#     LOGGING_CONFIG = {
#         "version": 1,
#         "disable_existing_loggers": True,
#         "filters": {"current_user": {"()": "modules.middleware.log.UserFilter"}},
#         "formatters": {
#             "json": {
#                 "format": fmt,
#                 "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
#             },
#             "error": {
#                 "format": fmt,
#                 "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
#             },
#             "standard": {"format": fmt},
#         },
#         "handlers": {
#             "console": {
#                 "level": console_log_level,
#                 "class": "logging.StreamHandler",
#                 "formatter": "standard",
#                 "stream": "ext://sys.stdout",
#                 "filters": ["current_user"],
#             },
#             "info_rotating_file_handler": {
#                 "level": "INFO",
#                 "formatter": "json",
#                 "class": "logging.handlers.RotatingFileHandler",
#                 "filename": logs_target,
#                 "mode": "a",
#                 "maxBytes": 1048576,
#                 "backupCount": 10,
#             },
#             "error_file_handler": {
#                 "level": "WARNING",
#                 "formatter": "error",
#                 "class": "logging.FileHandler",
#                 "filename": logs_error_target,
#                 "mode": "a",
#                 "filters": ["current_user"],
#             },
#             "critical_mail_handler": {
#                 "level": "CRITICAL",
#                 "formatter": "error",
#                 "class": "logging.handlers.SMTPHandler",
#                 "mailhost": "localhost",
#                 "fromaddr": "monitoring@domain.com",
#                 "toaddrs": ["dev@domain.com", "qa@domain.com"],
#                 "subject": "Critical error with application name",
#                 "filters": ["current_user"],
#             },
#         },
#         "loggers": {
#             "": {
#                 "level": console_log_level,
#                 "handlers": ["console"],
#             },
#             "__main__": {  # if __name__ == '__main__'
#                 "handlers": ["console"],
#                 "level": console_log_level,
#                 "propagate": False,
#             },
#             "src.modules": {
#                 "level": "WARNING",
#                 "propagate": False,
#                 "handlers": [
#                     "info_rotating_file_handler",
#                     "error_file_handler",
#                     "console",
#                 ],
#             },
#         },
#     }
#     return LOGGING_CONFIG
