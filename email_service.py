import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_PORT = int(os.getenv("MAIL_PORT", 465))
MAIL_SERVER = os.getenv("MAIL_SERVER")

def send_email(to_email: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg['From'] = MAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
       
        if MAIL_PORT == 465:
            server = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT)
        else:
            # Для порту 587 використовуємо звичайний SMTP + starttls
            server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
            server.starttls()
            
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(MAIL_FROM, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        raise ConnectionError(f"Failed to send email: {e}")