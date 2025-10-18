from django.contrib import admin
from .models import Badge, UserBadge, UserPoints

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'badge_type', 'points_required')
    list_filter = ('badge_type',)
    search_fields = ('name', 'description', 'criteria')

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at')
    list_filter = ('badge', 'earned_at')
    search_fields = ('user__username', 'badge__name')

@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_points', 'ideas_posted', 'comments_made', 'upvotes_received', 'resources_shared', 'events_organized')
    list_filter = ('total_points',)
    search_fields = ('user__username',)
    ordering = ('-total_points',)
