import smtplib
from email.message import EmailMessage
from core.config import settings
from typing import Optional


def send_email(subject: str, recipient: str, body: str) -> None:
    """
    Send an email using SMTP configured via environment variables (settings).

    Configure SMTP via env (.env):
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM

    This is a synchronous helper suitable to be used with FastAPI BackgroundTasks.
    """
    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    user = settings.SMTP_USER
    password = settings.SMTP_PASSWORD
    sender = settings.SMTP_FROM or user

    if not host or not port:
        raise RuntimeError("SMTP is not configured. Set SMTP_HOST and SMTP_PORT in environment.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body)

    # Try SSL first if port is typical 465, otherwise use STARTTLS
    if port == 465:
        with smtplib.SMTP_SSL(host, port) as smtp:
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as smtp:
            smtp.ehlo()
            try:
                smtp.starttls()
            except Exception:
                pass
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)


def send_verification_email(recipient: str, token: str, expires_minutes: int = 10) -> None:
    subject = "Your verification code"
    body = f"Your verification code is: {token}\nIt expires in {expires_minutes} minutes."
    send_email(subject, recipient, body)
