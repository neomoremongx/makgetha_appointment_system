from django.db import models
from django.utils import timezone
from datetime import date

# Create your models here.

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    ]
    
    SERVICE_CHOICES = [
        ('Divorce Consultation', 'Divorce Consultation'),
        ('Maintenance Hearing', 'Maintenance Hearing'),
        ('Civil Litigation', 'Civil Litigation'),
        ('Criminal Defense', 'Criminal Defense'),
        ('Estate Planning', 'Estate Planning'),
        ('Road Accident Fund', 'Road Accident Fund'),
        ('Other', 'Other'),
    ]
    
    appointment_id = models.CharField(max_length=10, unique=True, editable=False)
    client_name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    appointment_datetime = models.DateTimeField()
    attorney = models.CharField(max_length=100, default='M. Makgetha')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.appointment_id:
            # Generate appointment ID (APP001, APP002, etc.)
            last_appointment = Appointment.objects.order_by('-id').first()
            if last_appointment and last_appointment.appointment_id:
                last_num = int(last_appointment.appointment_id.replace('APP', ''))
                new_num = last_num + 1
            else:
                new_num = 1
            self.appointment_id = f'APP{new_num:03d}'
        
        # Ensure datetime is timezone aware
        if self.appointment_datetime and timezone.is_naive(self.appointment_datetime):
            self.appointment_datetime = timezone.make_aware(self.appointment_datetime)
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.appointment_id} - {self.client_name}"
    
    class Meta:
        ordering = ['-appointment_datetime']