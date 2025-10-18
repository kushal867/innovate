from django.contrib import admin
from .models import Resource, ResourceRating

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource_type', 'uploaded_by', 'is_curated', 'average_rating', 'created_at')
    list_filter = ('resource_type', 'is_curated', 'created_at', 'category')
    search_fields = ('title', 'description', 'uploaded_by__username', 'tags')

@admin.register(ResourceRating)
class ResourceRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'resource', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'resource__title', 'review')
