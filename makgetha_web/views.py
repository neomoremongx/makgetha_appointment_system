from django.shortcuts import render

# Create your views here.

def get_home(request):

    return render(request, 'home.html')


def get_about(request):

    return render(request, 'about.html')

def get_contact(request):

    return render(request, 'contact.html')

def get_services(request):

    return render(request, 'services.html')

def make_appointment(request):

    return render(request, 'appointment.html')



