import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()  # load .env values

SMTP_EMAIL = os.getenv("SMTP_EMAIL")  # your Gmail address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # 16-digit App Password


def send_email(to, subject, message):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        # Gmail SMTP settings
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)

        server.sendmail(SMTP_EMAIL, to, msg.as_string())
        server.quit()

        return True

    except Exception as e:
        print("Email error:", e)
        return False
