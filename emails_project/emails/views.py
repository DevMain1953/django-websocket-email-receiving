from django.shortcuts import render
from .models import EmailMessage


def message_list(request):
    return render(request, "email_list.html")
