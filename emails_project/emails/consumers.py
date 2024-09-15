import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from email.parser import BytesParser
from email.policy import default
from django.utils import timezone
import imaplib
from .utils import (
    get_email_service,
    convert_date_to_specified_format,
    get_message_body,
    get_and_save_message_attachments,
    serialize_datetime,
)


class EmailConsumer(AsyncWebsocketConsumer):
    IMAP_SERVERS = {
        "gmail": "imap.gmail.com",
        "yandex": "imap.yandex.com",
        "mail": "imap.mail.ru",
    }

    async def connect(self):
        self.room_name = "email"
        self.room_group_name = f"email_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        from .models import EmailAccount, EmailMessage

        email_account = await sync_to_async(EmailAccount.objects.first)()
        if email_account:
            email_service = get_email_service(email_account.email)
            imap_server = self.IMAP_SERVERS.get(email_service)

            if not imap_server:
                await self.send(
                    text_data=json.dumps({"error": "Unsupported email service."})
                )
                return

            mailbox = imaplib.IMAP4_SSL(imap_server)
            mailbox.login(email_account.email, email_account.password)
            mailbox.select("inbox")
            result, message_ids_with_spaces = mailbox.search(None, "ALL")

            message_ids = message_ids_with_spaces[0].split()
            total_messages = len(message_ids)

            for index, message_id in enumerate(message_ids):
                result, message_parts = mailbox.fetch(message_id, "(RFC822)")
                message = BytesParser(policy=default).parsebytes(message_parts[0][1])

                subject = message["subject"]
                sent_date = convert_date_to_specified_format(
                    message["date"], "%Y-%m-%d %H:%M:%S"
                )
                received_date = timezone.now()
                body = get_message_body(message)
                attachments = get_and_save_message_attachments(message)

                await sync_to_async(EmailMessage.objects.create)(
                    subject=subject,
                    sent_date=sent_date,
                    received_date=received_date,
                    body=body,
                    attachments=attachments,
                    email_account=email_account,
                )

                progress = int((index + 1) / total_messages * 100)
                await self.send_progress(
                    {"type": "send_progress", "progress": progress}
                )

                await self.send_message(
                    {
                        "type": "send_message",
                        "message": {
                            "subject": subject,
                            "sent_date": sent_date,
                            "received_date": serialize_datetime(received_date),
                            "body": body,
                            "attachments": attachments,
                        },
                    }
                )

    async def send_progress(self, event):
        progress = event["progress"]
        await self.send(
            text_data=json.dumps({"type": "progress", "progress": progress})
        )

    async def send_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"type": "message", "message": message}))
