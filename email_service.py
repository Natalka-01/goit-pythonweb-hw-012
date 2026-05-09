import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# SMTP configuration loaded from environment variables
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_PORT = int(os.getenv("MAIL_PORT", 465))
MAIL_SERVER = os.getenv("MAIL_SERVER")

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an email message via SMTP.

    Args:
        to_email (str): The recipient's email address.
        subject (str): The subject line of the email.
        body (str): The plain text content of the email.

    Returns:
        bool: True if the email was sent successfully.

    Raises:
        ConnectionError: If there is an issue connecting to or authenticating with the mail server.
    """
    msg = MIMEMultipart()
    msg['From'] = MAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Select the appropriate connection method based on the port
        if MAIL_PORT == 465:
            server = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT)
        else:
            # For port 587, use standard SMTP with STARTTLS
            server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
            server.starttls()
            
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(MAIL_FROM, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        raise ConnectionError(f"Failed to send email: {e}")