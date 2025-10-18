from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.urls import reverse
from .models import Group, GroupMembership, GroupDiscussion, DiscussionReply
from .forms import GroupForm, GroupDiscussionForm, DiscussionReplyForm
from notifications.models import Notification

def group_list(request):
    groups = Group.objects.select_related('created_by').annotate(
        member_count_total=Count('members', distinct=True)
    ).order_by('-created_at')
    
    category_filter = request.GET.get('category')
    if category_filter:
        groups = groups.filter(topic=category_filter)
    
    search_query = request.GET.get('q')
    if search_query:
        groups = groups.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(topic__icontains=search_query)
        ).distinct()
    
    paginator = Paginator(groups, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Group.objects.values_list('topic', flat=True).distinct().order_by('topic')
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_filter,
        'search_query': search_query,
    }
    return render(request, 'groups/list.html', context)

@login_required
def group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            
            GroupMembership.objects.create(
                group=group,
                user=request.user,
                role='admin'
            )
            
            messages.success(request, 'Your group has been created successfully!')
            return redirect('groups:detail', slug=group.slug)
    else:
        form = GroupForm()
    
    context = {'form': form}
    return render(request, 'groups/create.html', context)

def group_detail(request, slug):
    group = get_object_or_404(
        Group.objects.select_related('created_by')
        .prefetch_related('members', 'memberships__user', 'discussions__author'),
        slug=slug
    )
    
    discussions = group.discussions.select_related('author').annotate(
        reply_count=Count('replies', distinct=True)
    ).order_by('-pinned', '-created_at')
    
    members = group.memberships.select_related('user').order_by('-role', '-joined_at')
    
    is_member = False
    user_role = None
    if request.user.is_authenticated:
        membership = GroupMembership.objects.filter(group=group, user=request.user).first()
        is_member = membership is not None
        if membership:
            user_role = membership.role
    
    discussion_form = GroupDiscussionForm() if is_member else None
    
    context = {
        'group': group,
        'discussions': discussions,
        'members': members,
        'is_member': is_member,
        'user_role': user_role,
        'discussion_form': discussion_form,
    }
    return render(request, 'groups/detail.html', context)

@login_required
def group_edit(request, slug):
    group = get_object_or_404(Group, slug=slug)
    
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    if not membership or membership.role not in ['admin', 'moderator']:
        messages.error(request, 'Only group admins and moderators can edit the group.')
        return redirect('groups:detail', slug=slug)
    
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Group has been updated successfully!')
            return redirect('groups:detail', slug=group.slug)
    else:
        form = GroupForm(instance=group)
    
    context = {'form': form, 'group': group}
    return render(request, 'groups/edit.html', context)

@login_required
def group_delete(request, slug):
    group = get_object_or_404(Group, slug=slug)
    
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    if not membership or membership.role != 'admin':
        messages.error(request, 'Only group admins can delete the group.')
        return redirect('groups:detail', slug=slug)
    
    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Group has been deleted successfully!')
        return redirect('groups:list')
    
    context = {'group': group}
    return render(request, 'groups/delete_confirm.html', context)

@login_required
def group_join(request, slug):
    group = get_object_or_404(Group, slug=slug)
    
    membership, created = GroupMembership.objects.get_or_create(
        group=group,
        user=request.user,
        defaults={'role': 'member'}
    )
    
    if created:
        admin_memberships = GroupMembership.objects.filter(group=group, role='admin').select_related('user')
        for admin_membership in admin_memberships:
            if admin_membership.user != request.user:
                Notification.objects.create(
                    recipient=admin_membership.user,
                    sender=request.user,
                    notification_type='group_invite',
                    title='New Group Member',
                    message=f'{request.user.username} joined your group "{group.name}"',
                    link=reverse('groups:detail', kwargs={'slug': group.slug})
                )
        
        messages.success(request, f'You have joined "{group.name}"!')
    else:
        messages.info(request, 'You are already a member of this group.')
    
    return redirect('groups:detail', slug=slug)

@login_required
def group_leave(request, slug):
    group = get_object_or_404(Group, slug=slug)
    
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    
    if not membership:
        messages.info(request, 'You are not a member of this group.')
        return redirect('groups:detail', slug=slug)
    
    if membership.role == 'admin':
        admin_count = GroupMembership.objects.filter(group=group, role='admin').count()
        if admin_count <= 1:
            messages.error(request, 'You cannot leave the group as you are the only admin. Please assign another admin first or delete the group.')
            return redirect('groups:detail', slug=slug)
    
    membership.delete()
    messages.success(request, f'You have left "{group.name}".')
    return redirect('groups:list')

@login_required
def discussion_create(request, slug):
    group = get_object_or_404(Group, slug=slug)
    
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    if not membership:
        messages.error(request, 'You must be a member of the group to create discussions.')
        return redirect('groups:detail', slug=slug)
    
    if request.method == 'POST':
        form = GroupDiscussionForm(request.POST)
        if form.is_valid():
            discussion = form.save(commit=False)
            discussion.group = group
            discussion.author = request.user
            discussion.save()
            
            messages.success(request, 'Discussion created successfully!')
            return redirect('groups:discussion_detail', slug=slug, discussion_id=discussion.id)
    else:
        form = GroupDiscussionForm()
    
    context = {'form': form, 'group': group}
    return render(request, 'groups/discussion_create.html', context)

def discussion_detail(request, slug, discussion_id):
    group = get_object_or_404(Group, slug=slug)
    discussion = get_object_or_404(
        GroupDiscussion.objects.select_related('author', 'group')
        .prefetch_related('replies__author'),
        id=discussion_id,
        group=group
    )
    
    replies = discussion.replies.select_related('author').order_by('created_at')
    
    is_member = False
    if request.user.is_authenticated:
        is_member = GroupMembership.objects.filter(group=group, user=request.user).exists()
    
    reply_form = DiscussionReplyForm() if is_member else None
    
    context = {
        'group': group,
        'discussion': discussion,
        'replies': replies,
        'is_member': is_member,
        'reply_form': reply_form,
    }
    return render(request, 'groups/discussion_detail.html', context)

@login_required
def discussion_reply(request, slug, discussion_id):
    group = get_object_or_404(Group, slug=slug)
    discussion = get_object_or_404(GroupDiscussion, id=discussion_id, group=group)
    
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    if not membership:
        messages.error(request, 'You must be a member of the group to reply to discussions.')
        return redirect('groups:discussion_detail', slug=slug, discussion_id=discussion_id)
    
    if request.method == 'POST':
        form = DiscussionReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.discussion = discussion
            reply.author = request.user
            reply.save()
            
            if discussion.author != request.user:
                Notification.objects.create(
                    recipient=discussion.author,
                    sender=request.user,
                    notification_type='comment',
                    title='New Reply',
                    message=f'{request.user.username} replied to your discussion "{discussion.title}"',
                    link=reverse('groups:discussion_detail', kwargs={'slug': slug, 'discussion_id': discussion_id})
                )
            
            messages.success(request, 'Reply posted successfully!')
            return redirect('groups:discussion_detail', slug=slug, discussion_id=discussion_id)
    
    return redirect('groups:discussion_detail', slug=slug, discussion_id=discussion_id)
