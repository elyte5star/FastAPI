from pydantic import SecretStr, AfterValidator
import re
import uuid
from email_validator import validate_email, EmailNotValidError
from typing_extensions import Annotated
from fastapi.exceptions import RequestValidationError
from fastapi_mail.email_utils import DefaultChecker

# Password policy
SPECIAL_CHARS: set[str] = {
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


MIN_LENGTH: int = 5
MAX_LENGTH: int = 20
INCLUDES_SPECIAL_CHARS: bool = True
INCLUDES_NUMBERS: bool = True
INCLUDES_LOWERCASE: bool = True
INCLUDES_UPPERCASE: bool = True


def validate_password(v: SecretStr) -> SecretStr:
    min_length = MIN_LENGTH
    max_length = MAX_LENGTH
    includes_special_chars = INCLUDES_SPECIAL_CHARS
    includes_numbers = INCLUDES_NUMBERS
    includes_lowercase = INCLUDES_LOWERCASE
    includes_uppercase = INCLUDES_UPPERCASE
    special_chars = SPECIAL_CHARS

    if not isinstance(v.get_secret_value(), str):
        raise TypeError("string required")
    if len(v.get_secret_value()) < min_length or len(v.get_secret_value()) > max_length:
        raise RequestValidationError(
            f"length should be at least {min_length} but not more than 20"
        )

    if includes_numbers and not any(char.isdigit() for char in v.get_secret_value()):
        raise RequestValidationError("Password should have at least one numeral")

    if includes_uppercase and not any(char.isupper() for char in v.get_secret_value()):
        raise RequestValidationError(
            "Password should have at least one uppercase letter"
        )

    if includes_lowercase and not any(char.islower() for char in v.get_secret_value()):
        raise RequestValidationError(
            "Password should have at least one lowercase letter"
        )

    if includes_special_chars and not any(
        char in special_chars for char in v.get_secret_value()
    ):
        raise RequestValidationError(
            f"Password should have at least one of the symbols {special_chars}"
        )

    return v


ValidatePassword = Annotated[SecretStr, AfterValidator(validate_password)]


def username_validation(strParam: str) -> str:
    # username is between 4 and 25 characters
    if len(strParam) < 5 or len(strParam) > 20:
        raise RequestValidationError("length should be at least 5 but not more than 20")

    # start with a letter
    if not str(strParam[0]).isalpha():
        raise RequestValidationError("must start with letter")

    # can't end with an underscore
    if str(strParam[-1]) == "_":
        raise RequestValidationError("can't end with underscore")

    # contains only letters, numbers and underscore
    valid_grammar = set("abcdefghijklmnopqrstuvwxyz0123456789_")

    for ch in strParam:
        if ch.lower() not in valid_grammar:
            raise RequestValidationError(
                "can contains only letters,numbers and underscore"
            )
    return strParam


ValidateUsername = Annotated[str, AfterValidator(username_validation)]


def validate_mobile(value: str) -> str:
    rule = re.compile(
        r"^(?:(?:\(?(?:00|\+)([1-4]\d\d|[1-9]\d?)\)?)?[\-\.\ \\\/]?)?((?:\(?\d{1,}\)?[\-\.\ \\\/]?){0,})(?:[\-\.\ \\\/]?(?:#|ext\.?|extension|x)[\-\.\ \\\/]?(\d+))?$"
    )
    if len(value) > 20:
        raise RequestValidationError("length should not be more than 20")

    if not bool(rule.match(value)):
        RequestValidationError(f"{value} is an invalid mobile number")
    return value


ValidateTelephone = Annotated[str, AfterValidator(validate_mobile)]


def check_uuid(value: str) -> str:
    try:
        val = uuid.UUID(value, version=4)
        return str(val)
    except Exception:
        raise RequestValidationError(f"{value} is an invalid userid")


ValidateUUID = Annotated[str, AfterValidator(check_uuid)]


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


async def default_checker():
    checker = (
        DefaultChecker()
    )  # you can pass source argument for your own email domains
    await checker.fetch_temp_email_domains()  # require to fetch temporary email domains
    return checker
