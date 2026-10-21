import json
import smtplib
from email.message import EmailMessage

import streamlit as st


def send_submission_email(user_id: str, submission_reference: str, final_json: dict) -> None:
    
    config = st.secrets["email"]
    recipients = list(config["recipients"])
    
    if not recipients:
        raise ValueError("No email recipients are configured in Streamlit secrets.")

    # Prepare the email subjects
    message = EmailMessage()
    message["Subject"] = f"Annotation submission completed — {user_id}"
    message["From"] = config["smtp_user"]
    message["To"] = ", ".join(recipients)

    # Prepare the message content
    message.set_content(
        "An annotation submission has been completed.\n\n"
        f"Annotator ID: {user_id}\nSubmission reference: {submission_reference}\n\n"
        "The finalized annotation data is attached as a JSON file.\n"
    )

    # Attach the JSON file
    payload = json.dumps(final_json, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    safe_user_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in user_id)
    message.add_attachment(payload, maintype="application", subtype="json", filename=f"{safe_user_id}_annotations.json")

    # Send the email
    with smtplib.SMTP(config["smtp_host"], int(config["smtp_port"]), timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(config["smtp_user"], config["smtp_password"])
        server.send_message(message)
