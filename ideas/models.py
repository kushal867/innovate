from django.db import models
from django.conf import settings
from django.utils.text import slugify
from taggit.managers import TaggableManager

class Category(models.Model):
    CATEGORY_CHOICES = [
        ('tech', 'Technology'),
        ('education', 'Education'),
        ('social', 'Social Innovation'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

class Idea(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ideas')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='ideas')
    tags = TaggableManager()
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Idea.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def upvote_count(self):
        return self.upvotes.count()
    
    def comment_count(self):
        return self.comments.count()
    
    class Meta:
        ordering = ['-created_at']

class Comment(models.Model):
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.idea.title}"
    
    class Meta:
        ordering = ['created_at']

class Upvote(models.Model):
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='upvotes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='upvotes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} upvoted {self.idea.title}"
    
    class Meta:
        unique_together = ('idea', 'user')
        ordering = ['-created_at']

class Bookmark(models.Model):
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} bookmarked {self.idea.title}"
    
    class Meta:
        unique_together = ('idea', 'user')
        ordering = ['-created_at']
