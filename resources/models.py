from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator

class Resource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('document', 'Document'),
        ('video', 'Video'),
        ('link', 'Link'),
        ('tool', 'Tool'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    file = models.FileField(
        upload_to='resources/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'ppt', 'pptx', 'doc', 'docx', 'zip', 'py', 'js', 'html', 'css', 'mp4', 'txt'])],
        blank=True,
        null=True
    )
    link = models.URLField(max_length=500, blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_resources')
    is_curated = models.BooleanField(default=False)
    category = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=200, blank=True)
    download_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def average_rating(self):
        ratings = self.ratings.all()
        if ratings:
            return sum(r.rating for r in ratings) / len(ratings)
        return 0
    
    def rating_count(self):
        return self.ratings.count()
    
    class Meta:
        ordering = ['-created_at']

class ResourceRating(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resource_ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} rated {self.resource.title} - {self.rating} stars"
    
    class Meta:
        unique_together = ('resource', 'user')
        ordering = ['-created_at']
