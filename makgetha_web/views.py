from django.shortcuts import render
from django.core.mail import send_mail
# Create your views here.

def get_home(request):

    return render(request, 'home.html')


def get_about(request):

    return render(request, 'about.html')

def get_contact(request):
    if request.method == "POST":
        email = request.POST['email']
        phone = request.POST['phone']
        subject = request.POST['name']
        message = request.POST['message']
        
        send_mail(
            subject,
            message,
            email,
            ['info@mmakgethaattorneys.com'],
        )
        return render(request, 'contact.html')

    return render(request, 'contact.html')

def get_services(request):

    return render(request, 'services.html')

def make_appointment(request):

    return render(request, 'appointment.html')



