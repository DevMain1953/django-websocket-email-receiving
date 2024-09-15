from email.utils import parsedate_to_datetime
from email.message import EmailMessage
from django.conf import settings
from datetime import datetime
import os


def get_email_service(email: str) -> str | None:
    if email.endswith("@gmail.com"):
        return "gmail"
    elif email.endswith("@yandex.ru") or email.endswith("@ya.ru"):
        return "yandex"
    elif email.endswith("@mail.ru"):
        return "mail"
    else:
        return None


def convert_date_to_specified_format(date: str, format: str) -> str:
    parsed_date = parsedate_to_datetime(date)
    formatted_date = parsed_date.strftime(format)
    return formatted_date


def get_message_body(message: EmailMessage) -> str:
    body = ""
    if message.is_multipart():
        for part in message.iter_parts():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
    else:
        if message.get_content_type() == "text/plain":
            body = message.get_content()
    return body


def get_and_save_message_attachments(message: EmailMessage) -> list:
    filenames = []
    if message.is_multipart():
        for part in message.iter_parts():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()
                if filename:
                    file_content = part.get_payload(decode=True)
                    file_path = os.path.join(settings.MEDIA_ROOT, filename)
                    with open(file_path, "wb") as file:
                        file.write(file_content)
                    filenames.append(filename)
    return filenames


def serialize_datetime(datetime_to_serialize: datetime) -> str | datetime:
    if isinstance(datetime_to_serialize, datetime):
        return datetime_to_serialize.isoformat()
    return datetime_to_serialize
