from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, get_current_timezone, localtime
from .models import Appointment

# Login View
def login_view(request):
    """Handle user login"""
    # If user is already authenticated, redirect to home
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Set session expiry based on remember me checkbox
            if not remember_me:
                # Session expires when browser closes
                request.session.set_expiry(0)
            else:
                # Session expires in 2 weeks
                request.session.set_expiry(1209600)
            
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

# Logout View
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

# Protect existing views with login_required decorator
@login_required(login_url='login')

def get_home(request):
   """Render the main page with all appointments"""
    print("=" * 50)
    print("get_home view called")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"User: {request.user}")
    
    appointments = Appointment.objects.all().order_by('appointment_datetime')
    print(f"Appointments count via ORM: {appointments.count()}")
    for app in appointments:
        print(f"  - {app.appointment_id}: {app.client_name} at {app.appointment_datetime}")
    
    # Get current date in the local timezone
    now = localtime(timezone.now())
    today = now.date()
    tomorrow = today + timedelta(days=1)
    
    # Calculate week start (Monday)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Create datetime ranges for filtering
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    tomorrow_start = timezone.make_aware(datetime.combine(tomorrow, datetime.min.time()))
    tomorrow_end = timezone.make_aware(datetime.combine(tomorrow, datetime.max.time()))
    
    week_start_dt = timezone.make_aware(datetime.combine(week_start, datetime.min.time()))
    week_end_dt = timezone.make_aware(datetime.combine(week_end, datetime.max.time()))
    
    # Get today's appointments
    today_appointments = Appointment.objects.filter(
        appointment_datetime__range=[today_start, today_end],
        status='active'
    ).order_by('appointment_datetime')
    
    # Count today's appointments
    daily_appointments = today_appointments.count()
    
    # Get tomorrow's appointments
    tomorrow_appointments = Appointment.objects.filter(
        appointment_datetime__range=[tomorrow_start, tomorrow_end],
        status='active'
    ).order_by('appointment_datetime')
    
    # Count weekly appointments
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
        'today_appointments': today_appointments,
        'today_count': daily_appointments,
        'tomorrow_appointments': tomorrow_appointments,
        'tomorrow_count': tomorrow_appointments.count(),
        'new_appointment_id': new_appointment_id,
    }
    return render(request, "index.html", context)

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
    appointments = Appointment.objects.all().order_by('appointment_datetime') 
    
    # Calculate statistics
    now = localtime(timezone.now())
    today = now.date()
    tomorrow = today + timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Create datetime ranges for filtering
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    tomorrow_start = timezone.make_aware(datetime.combine(tomorrow, datetime.min.time()))
    tomorrow_end = timezone.make_aware(datetime.combine(tomorrow, datetime.max.time()))
    
    week_start_dt = timezone.make_aware(datetime.combine(week_start, datetime.min.time()))
    week_end_dt = timezone.make_aware(datetime.combine(week_end, datetime.max.time()))
    
    # Get today's appointments
    today_appointments = Appointment.objects.filter(
        appointment_datetime__range=[today_start, today_end],
        status='active'
    ).order_by('appointment_datetime')
    
    # Count today's appointments
    daily_appointments = today_appointments.count()
    
    # Get tomorrow's appointments
    tomorrow_appointments = Appointment.objects.filter(
        appointment_datetime__range=[tomorrow_start, tomorrow_end],
        status='active'
    ).order_by('appointment_datetime')
    
    # Count weekly appointments
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
        'today_appointments': today_appointments,
        'today_count': daily_appointments,
        'tomorrow_appointments': tomorrow_appointments,
        'tomorrow_count': tomorrow_appointments.count(),
        'search_result': appointment,
        'search_error': error,
        'search_id': appointment_id,
        'new_appointment_id': new_appointment_id,
    }
    return render(request, "index.html", context)

def create_appointment(request):
    """Create a new appointment"""
    if request.method == 'POST':
        client_name = request.POST.get('client_name')
        service_type = request.POST.get('service_type')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        
        # Combine date and time into a single datetime string
        appointment_datetime_str = f"{appointment_date}T{appointment_time}"
        
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
        
        # Check for duplicate date and time
        existing_appointment = Appointment.objects.filter(
            appointment_datetime=appointment_dt,
            status='active'
        ).exists()
        
        if existing_appointment:
            messages.error(request, 'This date and time is already booked. Please select a different time.')
            return redirect('home')
        
        appointment = Appointment.objects.create(
            client_name=client_name,
            service_type=service_type,
            appointment_datetime=appointment_dt,
            attorney='M. Makgetha',
            status='active'
        )
        appointment.save()
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
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        
        # Combine date and time into a single datetime string
        appointment_datetime_str = f"{appointment_date}T{appointment_time}"
        
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
        
        # Check for duplicate date and time (excluding the current appointment)
        existing_appointment = Appointment.objects.filter(
            appointment_datetime=appointment_dt,
            status='active'
        ).exclude(id=id).exists()
        
        if existing_appointment:
            messages.error(request, 'This date and time is already booked. Please select a different time.')
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

def get_appointment_detail(request, id):
    """Get appointment details for editing"""
    appointment = get_object_or_404(Appointment, id=id)

    return render(request, 'index.html', {'edit_appointment': appointment})


