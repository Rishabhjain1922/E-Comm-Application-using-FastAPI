import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from app.exception import EmailSendError

def send_reset_password_email(email_to: str, reset_token: str):
    """
    Send password reset email to user with the reset token
    """
    if not all([settings.SMTP_SERVER, settings.SMTP_PORT,
                settings.SMTP_USERNAME, settings.SMTP_PASSWORD,
                settings.EMAIL_FROM]):
        # If email config is missing, print token to console for development
        print(f"Password reset token for {email_to}: {reset_token}")
        return

    subject = "Password Reset Request"
    body = f"""
    You have requested to reset your password.
    Please use the following token to reset your password:

    Token: {reset_token}

    This token will expire in 15 minutes.
    If you didn't request this, please ignore this email.
    """

    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_FROM
        msg['To'] = email_to
        msg['Subject'] = subject

        # Add body to email
        msg.attach(MIMEText(body, 'plain'))

        # Create SMTP session
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

    except Exception as e:
        raise EmailSendError(detail=f"Failed to send email: {str(e)}")


def send_welcome_email(email_to: str, name: str):
    """
    Send welcome email to new users
    """
    if not all([settings.SMTP_SERVER, settings.SMTP_PORT,
                settings.SMTP_USERNAME, settings.SMTP_PASSWORD,
                settings.EMAIL_FROM]):
        print(f"Welcome email would be sent to {email_to}")
        return

    subject = "Welcome to Our E-commerce Platform"
    body = f"""
    Dear {name},

    Thank you for registering with our e-commerce platform!
    We're excited to have you on board.

    Happy shopping!
    """

    try:
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_FROM
        msg['To'] = email_to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

    except Exception as e:
        # Fail silently for welcome emails
        print(f"Error sending welcome email: {str(e)}")