import imaplib
import os
import time
from email import message_from_bytes
from dotenv import load_dotenv
from responder import run, get_checkpointer


# Load environment variables
load_dotenv()


# Email credentials
USERNAME = os.getenv("SENDER_EMAIL")
PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


def connect_to_email():
    """
    Establish a connection to the IMAP server and log in.
    Returns an IMAP4_SSL connection instance.
    """
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(USERNAME, PASSWORD)
        mail.select("inbox")
        return mail
    except imaplib.IMAP4.error as e:
        raise ConnectionError(f"Failed to connect to IMAP server: {e}")


def extract_email_body(email_message):
    """
    Extract the body content from an email message.
    Returns the plain text body, or "(No Body)" if none is found.
    """
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                body = part.get_payload(decode=True)
                return body.decode(part.get_content_charset() or "utf-8")
    else:
        body = email_message.get_payload(decode=True)
        return body.decode(email_message.get_content_charset() or "utf-8")

    return "(No Body)"


def process_email(mail, email_id):
    """
    Fetch and process a specific email by ID.
    Extracts and prints headers, body, and other metadata.
    """
    status, msg = mail.fetch(email_id, "(RFC822)")
    if status != "OK":
        print(f"Failed to fetch email with ID: {email_id}")
        return

    for response_part in msg:
        if isinstance(response_part, tuple):
            raw_email = response_part[1]
            if not raw_email:
                print(f"Email ID {email_id} has no content. Skipping...")
                continue

            try:
                email_message = message_from_bytes(raw_email)
                subject = email_message.get("Subject", "(No Subject)")
                sender = email_message.get("From", "(Unknown Sender)")
                message_id = email_message.get("Message-ID")
                in_reply_to = email_message.get("In-Reply-To")
                body = extract_email_body(email_message)

                # Debugging or further processing logic here
                print(f"Subject: {subject}")
                print(f"Sender: {sender}")
                print(f"Message ID: {message_id}")
                print(f"In-Reply-To: {in_reply_to}")
                print(f"Body:\n{body}")

                run(body, message_id, get_checkpointer())

                # TODO: Send response from AI model to the sender
                # TBD

            except Exception as e:
                print(f"Error parsing email ID {email_id}: {e}")


def check_new_emails(mail):
    """
    Check for new unread emails and process them.
    """
    status, messages = mail.search(None, "UNSEEN")
    if status != "OK":
        print("Failed to search for new emails.")
        return

    email_ids = messages[0].split()
    for email_id in email_ids:
        process_email(mail, email_id)


def main():
    """
    Main loop to check for new emails at regular intervals.
    """
    try:
        while True:
            print("Checking for new emails...")
            mail = connect_to_email()
            check_new_emails(mail)
            time.sleep(5)
    except ConnectionError as e:
        print(e)
    except KeyboardInterrupt:
        print("Exiting the program.")


if __name__ == "__main__":
    main()
