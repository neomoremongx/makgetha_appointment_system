from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_home, name='home'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('appointment/create/', views.create_appointment, name='create_appointment'),
    path('appointment/<int:id>/update/', views.update_appointment, name='update_appointment'),
    path('appointment/<int:id>/delete/', views.delete_appointment, name='delete_appointment'),
    path('appointment/<int:id>/', views.get_appointment_detail, name='appointment_detail'),
    path('search/', views.search_appointment, name='search_appointment'),
]