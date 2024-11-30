import hashlib
import imaplib
import email
from email.header import decode_header
import time
from main import run


# Email credentials
username = 'facker322@gmail.com'
password = 'iwyu ztpd rcwn rome'


def connect_to_email():
    """Establish a connection to the IMAP server and log in."""
    mail = imaplib.IMAP4_SSL('smtp.gmail.com')
    mail.login(username, password)
    mail.select('inbox')
    return mail


def normalize_subject(subject):
    """Normalize the subject by removing prefixes like 'Re:' and trimming whitespace."""
    if subject.lower().startswith("re:"):
        subject = subject[3:].strip()
    return subject


def process_email(mail, email_id):
    """Fetch and process a specific email by ID."""
    status, msg = mail.fetch(email_id, '(RFC822)')
    for response_part in msg:
        if isinstance(response_part, tuple):
            # Parse email
            email_message = email.message_from_bytes(response_part[1])

            # Decode email subject
            subject, encoding = decode_header(email_message['Subject'])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else 'utf-8')

            # Normalize the subject
            normalized_subject = normalize_subject(subject)

            # Extract 'From' field
            sender = email_message['From']

            # Combine 'From' and normalized 'Subject' for hashing
            combined_data = f"From: {sender}\nSubject: {normalized_subject}"

            # Generate SHA-256 hash
            hash_object = hashlib.sha256(combined_data.encode('utf-8'))
            email_hash = hash_object.hexdigest()

            # Extract email body
            if email_message.is_multipart():
                continue
            else:
                body = email_message.get_payload(decode=True).decode('utf-8')
                print(f'Body: {body}')

            run(body, email_hash)


def check_new_emails(mail, processed_emails):
    """Check for new emails and process them."""
    status, messages = mail.search(None, 'UNSEEN')  # Search for unread emails
    if status != 'OK':
        print("Failed to fetch emails.")
        return

    email_ids = messages[0].split()
    for email_id in email_ids:
        if email_id not in processed_emails:  # Check if email is already processed
            process_email(mail, email_id)
            break
            processed_emails.add(email_id)


if __name__ == "__main__":
    mail = connect_to_email()
    processed_emails = set()  # Track processed email IDs

    try:
        while True:
            print("Checking for new emails...")
            check_new_emails(mail, processed_emails)
            time.sleep(5)
    except KeyboardInterrupt:
        print("Exiting the program.")
        mail.logout()
