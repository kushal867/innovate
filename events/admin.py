from django.contrib import admin
from .models import Event, EventRegistration

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'organizer', 'start_date', 'end_date', 'is_online', 'registration_count')
    list_filter = ('event_type', 'is_online', 'start_date', 'created_at')
    search_fields = ('title', 'description', 'organizer__username', 'location')

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registered_at', 'attended')
    list_filter = ('attended', 'registered_at')
    search_fields = ('user__username', 'event__title')
