from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import Event, EventRegistration
from .forms import EventForm
from notifications.models import Notification

def event_list(request):
    event_type_filter = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    
    now = timezone.now()
    
    upcoming_events = Event.objects.filter(start_date__gte=now)
    past_events = Event.objects.filter(start_date__lt=now)
    
    if event_type_filter:
        upcoming_events = upcoming_events.filter(event_type=event_type_filter)
        past_events = past_events.filter(event_type=event_type_filter)
    
    if search_query:
        upcoming_events = upcoming_events.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
        past_events = past_events.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    upcoming_events = upcoming_events.annotate(attendee_count=Count('registrations')).order_by('start_date')
    past_events = past_events.annotate(attendee_count=Count('registrations')).order_by('-start_date')
    
    upcoming_paginator = Paginator(upcoming_events, 9)
    past_paginator = Paginator(past_events, 6)
    
    upcoming_page = request.GET.get('upcoming_page', 1)
    past_page = request.GET.get('past_page', 1)
    
    upcoming_events_page = upcoming_paginator.get_page(upcoming_page)
    past_events_page = past_paginator.get_page(past_page)
    
    context = {
        'upcoming_events': upcoming_events_page,
        'past_events': past_events_page,
        'event_type_filter': event_type_filter,
        'search_query': search_query,
        'event_types': Event.EVENT_TYPE_CHOICES,
    }
    return render(request, 'events/list.html', context)

@login_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('events:detail', pk=event.pk)
    else:
        form = EventForm()
    
    return render(request, 'events/create.html', {'form': form})

def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    attendees = event.registrations.select_related('user').all()
    
    is_registered = False
    if request.user.is_authenticated:
        is_registered = event.registrations.filter(user=request.user).exists()
    
    context = {
        'event': event,
        'attendees': attendees,
        'is_registered': is_registered,
        'is_organizer': request.user == event.organizer if request.user.is_authenticated else False,
        'is_full': event.is_full(),
        'attendee_count': event.registration_count(),
        'now': timezone.now(),
    }
    return render(request, 'events/detail.html', context)

@login_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    if event.organizer != request.user:
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('events:detail', pk=pk)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('events:detail', pk=pk)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/edit.html', {'form': form, 'event': event})

@login_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    if event.organizer != request.user:
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('events:detail', pk=pk)
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('events:list')
    
    return render(request, 'events/delete_confirm.html', {'event': event})

@login_required
def register_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    if event.is_full():
        messages.error(request, 'Sorry, this event is already full.')
        return redirect('events:detail', pk=pk)
    
    if event.registrations.filter(user=request.user).exists():
        messages.warning(request, 'You are already registered for this event.')
        return redirect('events:detail', pk=pk)
    
    if event.start_date < timezone.now():
        messages.error(request, 'Cannot register for past events.')
        return redirect('events:detail', pk=pk)
    
    EventRegistration.objects.create(event=event, user=request.user)
    
    Notification.objects.create(
        recipient=event.organizer,
        sender=request.user,
        notification_type='event_reminder',
        title='New Event Registration',
        message=f'{request.user.username} registered for your event "{event.title}"',
        link=f'/events/{event.pk}/'
    )
    
    messages.success(request, 'Successfully registered for the event!')
    return redirect('events:detail', pk=pk)

@login_required
def unregister_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    registration = event.registrations.filter(user=request.user).first()
    if not registration:
        messages.warning(request, 'You are not registered for this event.')
        return redirect('events:detail', pk=pk)
    
    if event.start_date < timezone.now():
        messages.error(request, 'Cannot unregister from past events.')
        return redirect('events:detail', pk=pk)
    
    registration.delete()
    messages.success(request, 'Successfully unregistered from the event.')
    return redirect('events:detail', pk=pk)
