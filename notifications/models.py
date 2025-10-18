from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('comment', 'New Comment'),
        ('upvote', 'Upvote'),
        ('follow', 'New Follower'),
        ('message', 'New Message'),
        ('group_invite', 'Group Invitation'),
        ('event_reminder', 'Event Reminder'),
        ('badge', 'Badge Earned'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.recipient.username}"
    
    class Meta:
        ordering = ['-created_at']
