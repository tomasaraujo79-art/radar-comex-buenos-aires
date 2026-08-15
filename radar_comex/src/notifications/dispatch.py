from __future__ import annotations

import smtplib
from email.message import EmailMessage

import requests


def notify(config: dict, jobs: list[dict], report_path: str) -> list[str]:
    messages: list[str] = []
    if not jobs:
        return messages
    integrations = config.get("integrations", {})
    if integrations.get("email", {}).get("enabled"):
        messages.append(_send_email(integrations["email"], jobs, report_path))
    if integrations.get("telegram", {}).get("enabled"):
        messages.append(_send_telegram(integrations["telegram"], jobs, report_path))
    return messages


def _send_email(config: dict, jobs: list[dict], report_path: str) -> str:
    msg = EmailMessage()
    msg["Subject"] = f"Radar COMEX: {len(jobs)} oportunidades nuevas"
    msg["From"] = config["email_from"]
    msg["To"] = config["email_to"]
    top = "\n".join(f"- {job['title']} - {job.get('company', '')}: {job.get('url', '')}" for job in jobs[:10])
    msg.set_content(f"Oportunidades encontradas:\n\n{top}\n\nReporte: {report_path}")
    with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as smtp:
        smtp.starttls()
        smtp.login(config["smtp_username"], config["smtp_password"])
        smtp.send_message(msg)
    return "email enviado"


def _send_telegram(config: dict, jobs: list[dict], report_path: str) -> str:
    top = "\n".join(f"- {job['title']} - {job.get('company', '')}\n{job.get('url', '')}" for job in jobs[:5])
    text = f"Radar COMEX encontro {len(jobs)} oportunidades.\n\n{top}\n\nReporte: {report_path}"
    url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
    response = requests.post(url, json={"chat_id": config["chat_id"], "text": text}, timeout=15)
    response.raise_for_status()
    return "telegram enviado"
