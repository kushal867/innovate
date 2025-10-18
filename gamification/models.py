from django.db import models
from django.conf import settings

class Badge(models.Model):
    BADGE_TYPE_CHOICES = [
        ('contributor', 'Top Contributor'),
        ('innovator', 'Innovative Thinker'),
        ('collaborator', 'Great Collaborator'),
        ('helper', 'Helpful Member'),
        ('expert', 'Domain Expert'),
        ('pioneer', 'Early Adopter'),
    ]
    
    name = models.CharField(max_length=100)
    badge_type = models.CharField(max_length=50, choices=BADGE_TYPE_CHOICES, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)
    criteria = models.TextField(help_text='Requirements to earn this badge')
    points_required = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_to')
    earned_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} earned {self.badge.name}"
    
    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-earned_at']

class UserPoints(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='points')
    total_points = models.IntegerField(default=0)
    ideas_posted = models.IntegerField(default=0)
    comments_made = models.IntegerField(default=0)
    upvotes_received = models.IntegerField(default=0)
    resources_shared = models.IntegerField(default=0)
    events_organized = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.total_points} points"
    
    class Meta:
        verbose_name_plural = 'User Points'
        ordering = ['-total_points']
