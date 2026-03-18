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

# ---------------------------------------------------------------------------
# Attorney username → model name mapping
# The superuser / admin (is_staff or is_superuser) bypasses this entirely.
# ---------------------------------------------------------------------------
ATTORNEY_MAP = {
    'makgetha': 'M. Makgetha',
    'mbhalati': 'M. Mbhalati',
    'tshitshiba': 'M. Tshitshiba',
}

# Minimum gap between consecutive appointments for the same attorney (minutes).
APPOINTMENT_GAP_MINUTES = 30


def get_attorney_for_user(user):
    """
    Returns the attorney name string if the logged-in user is an attorney,
    or None if the user is an admin (unrestricted access).
    """
    if user.is_superuser or user.is_staff:
        return None  # Admin — no restriction
    return ATTORNEY_MAP.get(user.username.lower())


def check_appointment_spacing(attorney, proposed_dt, exclude_id=None):
    """
    Returns None if the proposed datetime is free (≥ APPOINTMENT_GAP_MINUTES
    away from every other active appointment for this attorney).

    Returns the conflicting Appointment instance if there is a clash so the
    caller can build a meaningful error message.

    The window is *exclusive* — exactly APPOINTMENT_GAP_MINUTES apart is fine.
    """
    window_start = proposed_dt - timedelta(minutes=APPOINTMENT_GAP_MINUTES)
    window_end   = proposed_dt + timedelta(minutes=APPOINTMENT_GAP_MINUTES)

    qs = Appointment.objects.filter(
        attorney=attorney,
        status='active',
        appointment_datetime__gt=window_start,
        appointment_datetime__lt=window_end,
    )

    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)

    return qs.order_by('appointment_datetime').first()


def _build_dashboard_context(request, base_qs, extra=None):
    """
    Shared helper that builds the full context dict from a base queryset.
    `base_qs` is already filtered to the correct attorney scope (or global).
    """
    now = localtime(timezone.now())
    today = now.date()
    tomorrow = today + timedelta(days=1)

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end   = timezone.make_aware(datetime.combine(today, datetime.max.time()))

    tomorrow_start = timezone.make_aware(datetime.combine(tomorrow, datetime.min.time()))
    tomorrow_end   = timezone.make_aware(datetime.combine(tomorrow, datetime.max.time()))

    week_start_dt = timezone.make_aware(datetime.combine(week_start, datetime.min.time()))
    week_end_dt   = timezone.make_aware(datetime.combine(week_end,   datetime.max.time()))

    today_appointments = base_qs.filter(
        appointment_datetime__range=[today_start, today_end],
        status='active'
    ).order_by('appointment_datetime')

    tomorrow_appointments = base_qs.filter(
        appointment_datetime__range=[tomorrow_start, tomorrow_end],
        status='active'
    ).order_by('appointment_datetime')

    weekly_appointments = base_qs.filter(
        appointment_datetime__range=[week_start_dt, week_end_dt],
        status='active'
    ).count()

    new_appointment_id = request.session.pop('new_appointment_id', None)
    conflict_form_data = request.session.pop('conflict_form_data', None)

    context = {
        'appointments':          base_qs.order_by('appointment_datetime'),
        'daily_appointments':    today_appointments.count(),
        'weekly_appointments':   weekly_appointments,
        'today_appointments':    today_appointments,
        'today_count':           today_appointments.count(),
        'tomorrow_appointments': tomorrow_appointments,
        'tomorrow_count':        tomorrow_appointments.count(),
        'new_appointment_id':    new_appointment_id,
        'conflict_form_data':    conflict_form_data,
        # For the template to know who is viewing
        'is_admin':              get_attorney_for_user(request.user) is None,
        'current_attorney':      get_attorney_for_user(request.user),
    }
    if extra:
        context.update(extra)
    return context


# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(1209600)

            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def get_home(request):
    """Render the main page — scoped to attorney if not admin."""
    attorney = get_attorney_for_user(request.user)

    if attorney:
        base_qs = Appointment.objects.filter(attorney=attorney)
    else:
        base_qs = Appointment.objects.all()

    context = _build_dashboard_context(request, base_qs)
    return render(request, "index.html", context)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def search_appointment(request):
    """Search for an appointment by ID — respects attorney scope."""
    attorney = get_attorney_for_user(request.user)

    if attorney:
        base_qs = Appointment.objects.filter(attorney=attorney)
    else:
        base_qs = Appointment.objects.all()

    appointment_id = request.GET.get('id', '')
    appointment = None
    error = None

    if appointment_id:
        try:
            appointment = base_qs.get(appointment_id=appointment_id)
        except Appointment.DoesNotExist:
            error = f"No appointment found with ID: {appointment_id}"

    context = _build_dashboard_context(request, base_qs, extra={
        'search_result': appointment,
        'search_error':  error,
        'search_id':     appointment_id,
    })
    return render(request, "index.html", context)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def create_appointment(request):
    """Create a new appointment."""
    if request.method == 'POST':
        client_name      = request.POST.get('client_name')
        service_type     = request.POST.get('service_type')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        attorney_value   = request.POST.get('attorney')

        appointment_datetime_str = f"{appointment_date}T{appointment_time}"
        appointment_dt = datetime.fromisoformat(appointment_datetime_str)

        current_tz = get_current_timezone()
        appointment_dt = make_aware(appointment_dt, current_tz)
        now = localtime(timezone.now())

        # Reusable form data blob — reopens the modal pre-filled on any error
        form_data = {
            'mode':             'create',
            'client_name':      client_name,
            'service_type':     service_type,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'attorney':         attorney_value,
        }

        if appointment_dt < now:
            messages.error(request, 'Cannot create an appointment in the past. Please choose a future date and time.')
            request.session['conflict_form_data'] = form_data
            return redirect('home')

        conflict = check_appointment_spacing(attorney_value, appointment_dt)

        if conflict:
            gap = abs((conflict.appointment_datetime - appointment_dt).total_seconds() // 60)
            messages.error(
                request,
                f'Too close to an existing appointment ({conflict.client_name} at '
                f'{localtime(conflict.appointment_datetime).strftime("%H:%M")}). '
                f'Appointments must be at least {APPOINTMENT_GAP_MINUTES} minutes apart '
                f'— this one is only {int(gap)} minute{"s" if gap != 1 else ""} away.'
            )
            request.session['conflict_form_data'] = form_data
            return redirect('home')

        appointment = Appointment.objects.create(
            client_name=client_name,
            service_type=service_type,
            appointment_datetime=appointment_dt,
            attorney=attorney_value,
            status='active'
        )

        request.session['new_appointment_id'] = appointment.appointment_id

    return redirect('home')


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def update_appointment(request, id):
    """Update an existing appointment — attorneys can only update their own."""
    attorney = get_attorney_for_user(request.user)

    if attorney:
        appointment = get_object_or_404(Appointment, id=id, attorney=attorney)
    else:
        appointment = get_object_or_404(Appointment, id=id)

    if request.method == 'POST':
        client_name      = request.POST.get('client_name')
        service_type     = request.POST.get('service_type')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        attorney_value   = request.POST.get('attorney')

        appointment_datetime_str = f"{appointment_date}T{appointment_time}"
        appointment_dt = datetime.fromisoformat(appointment_datetime_str)

        current_tz = get_current_timezone()
        appointment_dt = make_aware(appointment_dt, current_tz)
        now = localtime(timezone.now())

        # Reusable form data blob — reopens the modal pre-filled on any error
        form_data = {
            'mode':             'edit',
            'edit_id':          id,
            'client_name':      client_name,
            'service_type':     service_type,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'attorney':         attorney_value,
        }

        if appointment_dt < now:
            messages.error(request, 'Cannot update an appointment to a past date. Please choose a future date and time.')
            request.session['conflict_form_data'] = form_data
            return redirect('home')

        conflict = check_appointment_spacing(attorney_value, appointment_dt, exclude_id=id)

        if conflict:
            gap = abs((conflict.appointment_datetime - appointment_dt).total_seconds() // 60)
            messages.error(
                request,
                f'Too close to an existing appointment ({conflict.client_name} at '
                f'{localtime(conflict.appointment_datetime).strftime("%H:%M")}). '
                f'Appointments must be at least {APPOINTMENT_GAP_MINUTES} minutes apart '
                f'— this one is only {int(gap)} minute{"s" if gap != 1 else ""} away.'
            )
            request.session['conflict_form_data'] = form_data
            return redirect('home')

        appointment.client_name          = client_name
        appointment.service_type         = service_type
        appointment.appointment_datetime = appointment_dt
        # Only admin can reassign attorney; attorney users keep their own name
        if not attorney:
            appointment.attorney = attorney_value
        appointment.save()

    return redirect('home')


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def delete_appointment(request, id):
    """Delete an appointment — attorneys can only delete their own."""
    attorney = get_attorney_for_user(request.user)

    if attorney:
        appointment = get_object_or_404(Appointment, id=id, attorney=attorney)
    else:
        appointment = get_object_or_404(Appointment, id=id)

    if request.method == 'POST':
        appt_id = appointment.appointment_id
        appointment.delete()
        messages.success(request, f'Appointment {appt_id} has been cancelled successfully.')

    return redirect('home')


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def get_appointment_detail(request, id):
    """Get appointment details for editing."""
    attorney = get_attorney_for_user(request.user)

    if attorney:
        appointment = get_object_or_404(Appointment, id=id, attorney=attorney)
    else:
        appointment = get_object_or_404(Appointment, id=id)

    return render(request, 'index.html', {'edit_appointment': appointment})
