import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Dict, Optional

def html_to_plain_text(html: str) -> str:
    text = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL)
    text = re.sub(r"<script.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())

def send_email(subject: str, html_content: str, config: Optional[Dict[str, str]] = None) -> bool:
    if config is None:
        config = {
            "SMTP_HOST": os.getenv("SMTP_HOST", ""),
            "SMTP_PORT": os.getenv("SMTP_PORT", "465"),
            "SMTP_USER": os.getenv("SMTP_USER", ""),
            "SMTP_PASS": os.getenv("SMTP_PASS", ""),
            "RECEIVER_EMAIL": os.getenv("RECEIVER_EMAIL", "")
        }
    
    host = str(config.get("SMTP_HOST", "")).strip()
    port = int(config.get("SMTP_PORT", 465) or 465)
    user = str(config.get("SMTP_USER", "")).strip()
    pwd = str(config.get("SMTP_PASS", "")).strip()
    receiver = str(config.get("RECEIVER_EMAIL", "")).strip()

    if not all([host, user, pwd, receiver]):
        print("[WARN] SMTP configuration is incomplete. Skipping email sending.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Morning Briefing <{user}>"
    msg["To"] = receiver
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=host if "." in host else "local")

    plain_content = html_to_plain_text(html_content)
    msg.attach(MIMEText(plain_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=20.0) as server:
                server.login(user, pwd)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20.0) as server:
                server.starttls()
                server.login(user, pwd)
                server.send_message(msg)
        print(f"[INFO] Morning news email sent successfully to {receiver}")
        return True
    except Exception as exc:
        print(f"[ERROR] Failed to send email via SMTP: {exc}")
        return False
