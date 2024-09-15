from django.db import models


class EmailAccount(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    SERVICE_CHOICES = [
        ("gmail", "Gmail"),
        ("yandex", "Yandex"),
        ("mail", "Mail.ru"),
    ]
    service = models.CharField(max_length=10, choices=SERVICE_CHOICES, default="gmail")


class EmailMessage(models.Model):
    subject = models.CharField(max_length=255)
    sent_date = models.DateTimeField()
    received_date = models.DateTimeField()
    body = models.TextField()
    attachments = models.JSONField()
    email_account = models.ForeignKey(
        EmailAccount, on_delete=models.CASCADE, related_name="messages"
    )
