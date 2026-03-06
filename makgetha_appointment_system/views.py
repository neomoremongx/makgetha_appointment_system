from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, get_current_timezone, localtime
from .models import Appointment

def get_home(request):
    """Render the main page with all appointments"""
    appointments = Appointment.objects.all()
    
    # Get current date in the local timezone
    now = localtime(timezone.now())
    today = now.date()
    
    # Calculate week start (Monday)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Debug print to console (check your terminal)
    print(f"Today's date: {today}")
    print(f"Week start: {week_start}, Week end: {week_end}")
    
    # Count appointments for today
    daily_appointments = 0
    for apt in appointments:
        # Convert appointment datetime to local time for comparison
        apt_local = localtime(apt.appointment_datetime)
        apt_date = apt_local.date()
        
        print(f"Appointment {apt.appointment_id}: {apt_date} - Status: {apt.status}")
        
        if apt_date == today and apt.status == 'active':
            daily_appointments += 1
    
    # Count appointments for this week
    weekly_appointments = 0
    for apt in appointments:
        apt_local = localtime(apt.appointment_datetime)
        apt_date = apt_local.date()
        
        if week_start <= apt_date <= week_end and apt.status == 'active':
            weekly_appointments += 1
    
    # Alternative using queryset filters (might be more efficient)
    # Make sure we're using the correct date range with timezone awareness
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    daily_filtered = Appointment.objects.filter(
        appointment_datetime__range=[today_start, today_end],
        status='active'
    ).count()
    
    week_start_dt = timezone.make_aware(datetime.combine(week_start, datetime.min.time()))
    week_end_dt = timezone.make_aware(datetime.combine(week_end, datetime.max.time()))
    
    weekly_filtered = Appointment.objects.filter(
        appointment_datetime__range=[week_start_dt, week_end_dt],
        status='active'
    ).count()
    
    print(f"Daily count (loop): {daily_appointments}, Daily count (filter): {daily_filtered}")
    print(f"Weekly count (loop): {weekly_appointments}, Weekly count (filter): {weekly_filtered}")
    
    # Check if there's a new appointment ID to show
    new_appointment_id = request.session.pop('new_appointment_id', None)
    
    context = {
        'appointments': appointments,
        'daily_appointments': daily_filtered,  # Use the filtered count
        'weekly_appointments': weekly_filtered,  # Use the filtered count
        'new_appointment_id': new_appointment_id,
    }
    return render(request, "index.html", context)

def create_appointment(request):
    """Create a new appointment"""
    if request.method == 'POST':
        client_name = request.POST.get('client_name')
        service_type = request.POST.get('service_type')
        appointment_datetime_str = request.POST.get('appointment_datetime')
        
        # Convert the string to a datetime object
        appointment_dt = datetime.fromisoformat(appointment_datetime_str)
        
        # Make the datetime aware using the current timezone from settings
        current_tz = get_current_timezone()
        appointment_dt = make_aware(appointment_dt, current_tz)
        
        # Get current time in the same timezone
        now = localtime(timezone.now())
        
        # Server-side validation for past dates
        if appointment_dt < now:
            messages.error(request, 'Cannot create appointment with past date.')
            return redirect('home')
        
        appointment = Appointment.objects.create(
            client_name=client_name,
            service_type=service_type,
            appointment_datetime=appointment_dt,
            attorney='M. Makgetha',
            status='active'
        )
        
        # Debug print
        print(f"Created appointment: {appointment.appointment_id} at {appointment.appointment_datetime}")
        print(f"Local time: {localtime(appointment.appointment_datetime)}")
        print(f"Today is: {localtime(timezone.now()).date()}")
        
        # Store the newly created appointment ID in session to show in modal
        request.session['new_appointment_id'] = appointment.appointment_id
        
    return redirect('home')

def update_appointment(request, id):
    """Update an existing appointment"""
    appointment = get_object_or_404(Appointment, id=id)
    
    if request.method == 'POST':
        client_name = request.POST.get('client_name')
        service_type = request.POST.get('service_type')
        appointment_datetime_str = request.POST.get('appointment_datetime')
        
        # Convert the string to a datetime object
        appointment_dt = datetime.fromisoformat(appointment_datetime_str)
        
        # Make the datetime aware using the current timezone from settings
        current_tz = get_current_timezone()
        appointment_dt = make_aware(appointment_dt, current_tz)
        
        # Get current time in the same timezone
        now = localtime(timezone.now())
        
        # Server-side validation for past dates
        if appointment_dt < now:
            messages.error(request, 'Cannot update appointment to a past date.')
            return redirect('home')
        
        appointment.client_name = client_name
        appointment.service_type = service_type
        appointment.appointment_datetime = appointment_dt
        appointment.save()
    
    return redirect('home')

def delete_appointment(request, id):
    """Permanently delete an appointment"""
    appointment = get_object_or_404(Appointment, id=id)
    
    if request.method == 'POST':
        # Permanently delete the appointment from database
        appointment.delete()
        messages.success(request, f'Appointment {appointment.appointment_id} has been cancelled successfully.')
    
    return redirect('home')

def search_appointment(request):
    """Search for an appointment by ID"""
    appointment_id = request.GET.get('id', '')
    appointment = None
    error = None
    
    if appointment_id:
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)
        except Appointment.DoesNotExist:
            error = f"No appointment found with ID: {appointment_id}"
    
    # Get all appointments for the main list
    appointments = Appointment.objects.all()
    
    # Calculate statistics
    now = localtime(timezone.now())
    today = now.date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Use datetime range for accurate filtering
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    daily_appointments = Appointment.objects.filter(
        appointment_datetime__range=[today_start, today_end],
        status='active'
    ).count()
    
    week_start_dt = timezone.make_aware(datetime.combine(week_start, datetime.min.time()))
    week_end_dt = timezone.make_aware(datetime.combine(week_end, datetime.max.time()))
    
    weekly_appointments = Appointment.objects.filter(
        appointment_datetime__range=[week_start_dt, week_end_dt],
        status='active'
    ).count()
    
    # Check if there's a new appointment ID to show
    new_appointment_id = request.session.pop('new_appointment_id', None)
    
    context = {
        'appointments': appointments,
        'daily_appointments': daily_appointments,
        'weekly_appointments': weekly_appointments,
        'search_result': appointment,
        'search_error': error,
        'search_id': appointment_id,
        'new_appointment_id': new_appointment_id,
    }
    return render(request, "index.html", context)

def get_appointment_detail(request, id):
    """Get appointment details for editing"""
    appointment = get_object_or_404(Appointment, id=id)
    return render(request, 'index.html', {'edit_appointment': appointment})