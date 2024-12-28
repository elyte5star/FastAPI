from typing import Any
from typing import Dict
from pydantic import SecretStr, GetCoreSchemaHandler
from pydantic.v1.utils import update_not_none
import re
import uuid
from email_validator import validate_email, EmailNotValidError


class Password(SecretStr):
    """Pydantic type for password"""

    special_chars = {
        "$",
        "@",
        "#",
        "%",
        "!",
        "^",
        "&",
        "*",
        "(",
        ")",
        "-",
        "_",
        "+",
        "=",
        "{",
        "}",
        "[",
        "]",
    }

    min_length = 5
    includes_special_chars = False
    includes_numbers = False
    includes_lowercase = False
    includes_uppercase = False

    @classmethod
    def __get_pydantic_json_schema__(
        cls, field_schema: Dict[str, Any], handler: GetCoreSchemaHandler
    ) -> None:
        update_not_none(
            field_schema,
            minLength=cls.min_length,
            includesNumbers=cls.includes_numbers,
            includesLowercase=cls.includes_lowercase,
            includesUppercase=cls.includes_uppercase,
            includesSpecialChars=cls.includes_special_chars,
            specialChars=cls.special_chars,
        )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")

        if len(v) < cls.min_length or len(v) > 20:
            raise ValueError(
                f"length should be at least {cls.min_length} but not more than 20"
            )

        if cls.includes_numbers and not any(char.isdigit() for char in v):
            raise ValueError("Password should have at least one numeral")

        if cls.includes_uppercase and not any(char.isupper() for char in v):
            raise ValueError("Password should have at least one uppercase letter")

        if cls.includes_lowercase and not any(char.islower() for char in v):
            raise ValueError("Password should have at least one lowercase letter")

        if cls.includes_special_chars and not any(
            char in cls.special_chars for char in v
        ):
            raise ValueError(
                f"Password should have at least one of the symbols {cls.special_chars}"
            )

        return cls(v)


def username_validation(strParam: str) -> str:

    # username is between 4 and 25 characters
    if len(strParam) < 5 or len(strParam) > 20:
        raise ValueError("length should be at least 5 but not more than 20")

    # start with a letter
    if not str(strParam[0]).isalpha():
        raise ValueError("must start with letter")

    # can't end with an underscore
    if str(strParam[-1]) == "_":
        raise ValueError("can't end with underscore")

    # contains only letters, numbers and underscore
    valid_grammar = set("abcdefghijklmnopqrstuvwxyz0123456789_")

    for ch in strParam:
        if ch.lower() not in valid_grammar:
            raise ValueError("can contains only letters,numbers and underscore")
    return strParam


def validate_mobile(value: str) -> str:
    rule = re.compile(
        r"^(?:(?:\(?(?:00|\+)([1-4]\d\d|[1-9]\d?)\)?)?[\-\.\ \\\/]?)?((?:\(?\d{1,}\)?[\-\.\ \\\/]?){0,})(?:[\-\.\ \\\/]?(?:#|ext\.?|extension|x)[\-\.\ \\\/]?(\d+))?$"
    )

    if not bool(rule.match(value)):
        ValueError(f"{value} is an invalid mobile number")
    return value


def check_uuid(value: str) -> str:
    try:
        val = uuid.UUID(value, version=4)
        return str(val)
    except ValueError:
        raise ValueError(f"{value} is an invalid uuid")


def is_valid_email(email: str) -> tuple[bool, str]:
    try:

        # Check that the email address is valid. Turn on check_deliverability
        # for first-time validations like on account creation pages (but not
        # login pages).
        emailinfo = validate_email(email, check_deliverability=False)

        # After this point, use only the normalized form of the email address,
        # especially before going to a database query.
        email = emailinfo.normalized
        return (True, email)
    except EmailNotValidError:
        return (False, email)
