from modules.settings.configuration import ApiConfig
from fastapi_mail import (
    FastMail,
    MessageSchema,
    MessageType,
)
from modules.repository.request_models.user import EmailRequestSchema
from fastapi_mail.errors import ConnectionErrors
from modules.repository.validators.base import default_checker
from fastapi import BackgroundTasks, Depends
from fastapi_mail.email_utils import DefaultChecker
from itsdangerous import URLSafeTimedSerializer, BadTimeSignature, SignatureExpired


class EmailHandler:
    def __init__(self, config: ApiConfig):
        self.fm = FastMail(config.email_config)
        self.config = config

    async def send_plain_text(self, req: EmailRequestSchema) -> bool:
        message = MessageSchema(
            subject=req.body["subject"],
            recipients=req.recipients,
            body=req.body["message"],
            subtype=MessageType.plain,
        )
        try:
            await self.fm.send_message(message)
            return True  # req.req_success(f"Message sent to {req.recipients}")
        except ConnectionErrors as e:
            self.config.logger.error("Couldn't not send email", e)
            return False  # req.req_failure("Couldn't not send email")

    async def send_email_to_user(self, req: EmailRequestSchema) -> bool:
        message = MessageSchema(
            subject=req.body["subject"],
            recipients=req.recipients,
            body=req.body["message"],
            subtype=MessageType.plain,
        )
        try:
            await self.fm.send_message(message, template_name=req.template_name)
            return True
        except ConnectionErrors as e:
            self.config.logger.error("Couldn't not send email", e)
            return False  # req.req_failure("Couldn't not send email")

    async def send_invoice(
        self, background_tasks: BackgroundTasks, req: EmailRequestSchema
    ) -> bool:
        message = MessageSchema(
            subject=req.body["subject"],
            recipients=req.recipients,
            body=req.body["message"],
            subtype=MessageType.html,
            attachments=[req.file],
        )
        try:
            background_tasks.add_task(self.fm.send_message, message, req.template_name)
            return True  # req.req_success(f"Invoice sent to {req.emails}")
        except ConnectionErrors as e:
            self.config.logger.error("Couldn't not send invoice", e)
            return False  # req.req_failure("Couldn't not send invoice")

    async def block_email_address(
        self,
        email: str,
        checker: DefaultChecker = Depends(default_checker),
    ) -> bool:
        await checker.blacklist_add_email(email)
        return True

    async def del_blocked_email_address(
        self,
        email: str,
        checker: DefaultChecker = Depends(default_checker),
    ) -> bool:
        _ = await checker.blacklist_rm_email(email)
        return True

    def generate_confirmation_token(self, email: str):
        serializer = URLSafeTimedSerializer(
            self.cf.secret_key, salt=self.cf.security_salt
        )
        return serializer.dumps(email)

    def verify_email_token(self, token: str, expiration: int = 3600) -> bool:
        serializer = URLSafeTimedSerializer(self.config.secret_key)
        try:
            _ = serializer.loads(token, salt=self.config.rounds, max_age=expiration)
            return True
        except SignatureExpired:
            return False
        except BadTimeSignature:
            return False

    async def check_disposable_email(
        self,
        email: str,
        checker: DefaultChecker = Depends(default_checker),
    ) -> bool:
        domain = email.split("@")[-1]
        if await checker.is_disposable(domain):
            return True
        return False
