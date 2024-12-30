from typing import Optional


class Email:
    _from: Optional[str] = None
    to: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None

    def __init__(self, subject, content):
        self.subject = subject
        self.content = content

    def __str__(self):
        return f"Subject: {self.subject}\n{self.content}"


def send_email(sender_email, sender_password, receiver_email, subject, body, filename):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    part.add_header("Content-Disposition", f"attachment; filename= {filename}")

    msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()
