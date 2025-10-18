from django.contrib import admin
from .models import Group, GroupMembership, GroupDiscussion, DiscussionReply

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'topic', 'created_by', 'is_private', 'member_count', 'created_at')
    list_filter = ('is_private', 'topic', 'created_at')
    search_fields = ('name', 'description', 'topic', 'created_by__username')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__username', 'group__name')

@admin.register(GroupDiscussion)
class GroupDiscussionAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'author', 'pinned', 'created_at')
    list_filter = ('pinned', 'created_at', 'group')
    search_fields = ('title', 'content', 'author__username', 'group__name')

@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = ('author', 'discussion', 'content_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username', 'discussion__title')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
