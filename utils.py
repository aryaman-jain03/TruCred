def get_grade(score):
    """
    Converts numerical score into a trust grade.
    """
    if score >= 80:
        return "A"
    elif score >= 50:
        return "B"
    else:
        return "C"

import smtplib
import ssl
from email.message import EmailMessage
import os

def send_email_with_pdf(to_email, subject, body, pdf_path):
    # Sanitize header fields
    to_email = to_email.strip().replace('\n', '').replace('\r', '')
    subject = subject.strip().replace('\n', '').replace('\r', '')

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = os.environ.get("SENDER_EMAIL", "aryaman.parun@gmail.com")
    msg['To'] = to_email
    msg.set_content(body)

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
        msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename="TruCred_Report.pdf")

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.environ.get("SENDER_EMAIL", "aryaman.parun@gmail.com")
    sender_password = os.environ.get("SENDER_PASSWORD", "igut vwsr xswg ouun")

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
