import logging
import sys
from logging.handlers import TimedRotatingFileHandler, SMTPHandler
from os import path, getenv
from pathlib import Path
from pythonjsonlogger import jsonlogger
from modules.settings.configuration import ApiConfig


base_dir = Path(__file__).parent.parent.parent.parent.parent
logs_target = path.join(base_dir / "logs", "api.log")
logs_error_target = path.join(base_dir / "logs", "error.log")


fmt = "%(levelname)s::%(asctime)s :: %(name)s :: %(funcName)s :: Run by: %(current_user)s :: %(message)s"


class UserFilter(logging.Filter):
    def filter(self, record) -> bool:
        record.current_user = str(getenv("current_user", "API"))
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


FORMATTER = logging.Formatter(fmt)


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    console_handler.addFilter(UserFilter())
    return console_handler


def smtp_log_handler(cfg: ApiConfig):
    smtp_handler = SMTPHandler(
        mailhost=[cfg.mail_server, cfg.mail_port],
        fromaddr=cfg.email,
        toaddrs=["checkuti@gmail.com"],
        subject="Exceptional Log",
        credentials=(cfg.mail_username, cfg.mail_password),
        secure=None,
    )
    smtp_handler.setFormatter(FORMATTER)
    smtp_handler.addFilter(UserFilter())
    smtp_handler.setLevel(logging.CRITICAL)
    return smtp_handler


def info_file_handler(filename: str = logs_target):
    file_handler = TimedRotatingFileHandler(filename, when="midnight")
    formatter = CustomJsonFormatter(fmt)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(UserFilter())
    file_handler.setLevel(logging.INFO)
    return file_handler


def error_file_handler(filename: str = logs_error_target):
    file_handler = TimedRotatingFileHandler(filename, when="midnight")
    formatter = CustomJsonFormatter(fmt)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(UserFilter())
    file_handler.setLevel(logging.WARNING)
    return file_handler
