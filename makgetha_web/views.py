from django.shortcuts import render
import resend
import os
from django.core.mail import send_mail
from dotenv import load_dotenv
# Create your views here.

load_dotenv()
def get_home(request):

    return render(request, 'home.html')


def get_about(request):

    return render(request, 'about.html')

def get_contact(request):
    if request.method == "POST":
        name    = request.POST['name']
        email   = request.POST['email']
        phone   = request.POST['phone']
        message = request.POST['message']

        resend.api_key = os.environ['RESEND_API_KEY2']

        resend.Emails.send({
        "from":"info@mmakgethaattorneys.com",
        "to": "info@mmakgethaattorneys.com",  # ← your verified Resend email
         "reply_to": email,
        "subject": f"Website enquiry from {name}",
        "html": f"""{message}""",
         })

        return render(request, 'contact.html', {'sent': True})

    return render(request, 'contact.html')

def get_services(request):

    return render(request, 'services.html')

def make_appointment(request):
    if request.method == "POST":
        name    = request.POST['fullname']
        email   = request.POST['email']
        phone   = request.POST['phone']
        whatsapp = request.POST['whatsapp']
        service = request.POST['service']
        message = request.POST['message']
        description = request.POST['description']

        resend.api_key = os.environ['RESEND_API_KEY2']

        resend.Emails.send({
        "from":"info@mmakgethaattorneys.com",
        "to": "info@mmakgethaattorneys.com",  # ← your verified Resend email
         "reply_to": email,
        "subject": f"Website enquiry from {name}",
        "html": f"""{message}""",
         })

        return render(request, 'appointment.html', {'sent': True})

    return render(request, 'appointment.html')



