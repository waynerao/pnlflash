import logging
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime

from config import SMTP_HOST, SMTP_PORT, FROM_ADDRESS

logger = logging.getLogger(__name__)


def send_email(html, subject, to_list, cc_list):
    # Stub: save as .eml file (openable in Outlook) and log
    output_dir = Path(__file__).parent / "output" / "sent_emails"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    msg = MIMEText(html, "html")
    msg["Subject"] = subject
    msg["From"] = FROM_ADDRESS
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)

    file_path = output_dir / f"{timestamp}.eml"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(msg.as_string())

    logger.info(f"[STUB] Email sent - Subject: {subject}")
    logger.info(f"[STUB] To: {to_list}, CC: {cc_list}")
    logger.info(f"[STUB] Saved to: {file_path}")
    logger.info(f"[STUB] SMTP would use {SMTP_HOST}:{SMTP_PORT} from {FROM_ADDRESS}")
    return str(file_path)
