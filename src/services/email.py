from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import SecretStr
from typing import Optional

from pathlib import Path
from src.services.auth import auth_service
from src.config.config import settings

# smtp

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME="Contacts App",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_templated_email(
    email: str,
    username: str,
    host: str,
    subject: str,
    template_name: str,
    reset_link: Optional[str] = None,
    token: Optional[str] = None,
):
    """Send an email rendered from a Jinja2/HTML template.

    Args:
        email: Recipient email address.
        username: Recipient username for personalization.
        host: Base URL of the backend (used for links).
        subject: Email subject line.
        template_name: Name of the template file in templates folder.
        reset_link: Optional URL for password reset flow.
        token: Optional confirmation/reset token to embed.
    """
    try:
        if not reset_link:
            token = auth_service.create_email_token({"sub": email})

        message = MessageSchema(
            subject=subject,
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token,
                "reset_link": reset_link,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_name)
        print(f"Email ({subject}) sent to {email}")
    except ConnectionErrors as err:
        print(f"Connection error: {err}")
    except Exception as err:
        print(f"General error: {err}")


async def send_email(email: str, username: str, host: str):
    """Send email confirmation message with token link to the user."""
    await send_templated_email(
        email=email,
        username=username,
        host=host,
        subject="Confirm your email",
        template_name="email_template.html",
    )


async def send_reset_email(email: str, username: str, host: str, token: str):
    """Send password reset email with generated reset_link."""
    reset_link = f"{host}api/auth/reset_password/{token}"
    print(f"Generated reset_link: {reset_link}")
    await send_templated_email(
        email=email,
        username=username,
        host=host,
        subject="Reset Your Password",
        template_name="reset_password_template.html",
        reset_link=reset_link,
        token=token,
    )
