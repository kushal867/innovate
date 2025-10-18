from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'skill_level', 'region', 'is_staff', 'created_at')
    list_filter = ('role', 'skill_level', 'region', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'bio', 'expertise')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'bio', 'expertise', 'profile_picture', 'region', 'skill_level', 'followers')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'bio', 'expertise', 'region', 'skill_level')
        }),
    )
    
    filter_horizontal = ('followers', 'groups', 'user_permissions')
