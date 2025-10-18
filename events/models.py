from django.db import models
from django.conf import settings

class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('webinar', 'Webinar'),
        ('workshop', 'Workshop'),
        ('hackathon', 'Hackathon'),
        ('meetup', 'Meetup'),
        ('conference', 'Conference'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organized_events')
    location = models.CharField(max_length=200, blank=True)
    is_online = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    max_participants = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def registration_count(self):
        return self.registrations.count()
    
    def is_full(self):
        if self.max_participants:
            return self.registration_count() >= self.max_participants
        return False
    
    class Meta:
        ordering = ['start_date']

class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} registered for {self.event.title}"
    
    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-registered_at']
