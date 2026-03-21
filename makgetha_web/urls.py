from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_home, name='home'),
    path('home', views.get_home, name='home'),
    path('about', views.get_about, name='about'),
    path('services', views.get_services, name='services'),
    path('contact', views.get_contact, name='contact'),
    path('appointment', views.make_appointment, name='appointment'),
]