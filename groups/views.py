from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.urls import reverse

from .models import Group, GroupMembership, GroupDiscussion, DiscussionReply
from .forms import GroupForm, GroupDiscussionForm, DiscussionReplyForm
from notifications.models import Notification


# -------------------- Helpers --------------------
def get_membership(user, group):
    if not user.is_authenticated:
        return None
    return GroupMembership.objects.filter(group=group, user=user).first()


def is_admin_or_moderator(membership):
    return membership and membership.role in ['admin', 'moderator']


def is_admin(membership):
    return membership and membership.role == 'admin'


def notify_users(users, sender, title, message, link, notification_type):
    notifications = [
        Notification(
            recipient=user,
            sender=sender,
            title=title,
            message=message,
            link=link,
            notification_type=notification_type
        )
        for user in users if user != sender
    ]
    Notification.objects.bulk_create(notifications)


# -------------------- Group List --------------------
def group_list(request):
    groups = (
        Group.objects.select_related('created_by')
        .annotate(member_count_total=Count('members', distinct=True))
        .order_by('-created_at')
    )

    category = request.GET.get('category')
    search = request.GET.get('q')

    if category:
        groups = groups.filter(topic=category)

    if search:
        groups = groups.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(topic__icontains=search)
        ).distinct()

    paginator = Paginator(groups, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'categories': Group.objects.values_list('topic', flat=True).distinct(),
        'current_category': category,
        'search_query': search,
    }
    return render(request, 'groups/list.html', context)


# -------------------- Create --------------------
@login_required
def group_create(request):
    form = GroupForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        group = form.save(commit=False)
        group.created_by = request.user
        group.save()

        GroupMembership.objects.create(
            group=group,
            user=request.user,
            role='admin'
        )

        messages.success(request, 'Group created successfully!')
        return redirect('groups:detail', slug=group.slug)

    return render(request, 'groups/create.html', {'form': form})


# -------------------- Detail --------------------
def group_detail(request, slug):
    group = get_object_or_404(
        Group.objects.select_related('created_by')
        .prefetch_related('memberships__user', 'discussions__author'),
        slug=slug
    )

    membership = get_membership(request.user, group)

    discussions = (
        group.discussions.select_related('author')
        .annotate(reply_count=Count('replies', distinct=True))
        .order_by('-pinned', '-created_at')
    )

    context = {
        'group': group,
        'discussions': discussions,
        'members': group.memberships.select_related('user'),
        'is_member': bool(membership),
        'user_role': membership.role if membership else None,
        'discussion_form': GroupDiscussionForm() if membership else None,
    }
    return render(request, 'groups/detail.html', context)


# -------------------- Edit --------------------
@login_required
def group_edit(request, slug):
    group = get_object_or_404(Group, slug=slug)
    membership = get_membership(request.user, group)

    if not is_admin_or_moderator(membership):
        messages.error(request, 'Permission denied.')
        return redirect('groups:detail', slug=slug)

    form = GroupForm(request.POST or None, request.FILES or None, instance=group)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Group updated successfully!')
        return redirect('groups:detail', slug=group.slug)

    return render(request, 'groups/edit.html', {'form': form, 'group': group})


# -------------------- Delete --------------------
@login_required
def group_delete(request, slug):
    group = get_object_or_404(Group, slug=slug)
    membership = get_membership(request.user, group)

    if not is_admin(membership):
        messages.error(request, 'Only admins can delete this group.')
        return redirect('groups:detail', slug=slug)

    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Group deleted.')
        return redirect('groups:list')

    return render(request, 'groups/delete_confirm.html', {'group': group})


# -------------------- Join / Leave --------------------
@login_required
def group_join(request, slug):
    group = get_object_or_404(Group, slug=slug)

    membership, created = GroupMembership.objects.get_or_create(
        group=group,
        user=request.user,
        defaults={'role': 'member'}
    )

    if created:
        admins = GroupMembership.objects.filter(
            group=group, role='admin'
        ).values_list('user', flat=True)

        notify_users(
            users=[user for user in Group.objects.filter(id__in=admins)],
            sender=request.user,
            title='New Member',
            message=f'{request.user.username} joined "{group.name}"',
            link=reverse('groups:detail', kwargs={'slug': group.slug}),
            notification_type='group'
        )

        messages.success(request, f'Joined "{group.name}"')
    else:
        messages.info(request, 'Already a member.')

    return redirect('groups:detail', slug=slug)


@login_required
def group_leave(request, slug):
    group = get_object_or_404(Group, slug=slug)
    membership = get_membership(request.user, group)

    if not membership:
        messages.info(request, 'Not a member.')
        return redirect('groups:detail', slug=slug)

    if membership.role == 'admin':
        if GroupMembership.objects.filter(group=group, role='admin').count() <= 1:
            messages.error(request, 'Assign another admin before leaving.')
            return redirect('groups:detail', slug=slug)

    membership.delete()
    messages.success(request, f'Left "{group.name}"')
    return redirect('groups:list')


# -------------------- Discussion --------------------
@login_required
def discussion_create(request, slug):
    group = get_object_or_404(Group, slug=slug)
    membership = get_membership(request.user, group)

    if not membership:
        messages.error(request, 'Join group to post.')
        return redirect('groups:detail', slug=slug)

    form = GroupDiscussionForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        discussion = form.save(commit=False)
        discussion.group = group
        discussion.author = request.user
        discussion.save()

        return redirect('groups:discussion_detail', slug=slug, discussion_id=discussion.id)

    return render(request, 'groups/discussion_create.html', {'form': form, 'group': group})


def discussion_detail(request, slug, discussion_id):
    discussion = get_object_or_404(
        GroupDiscussion.objects.select_related('author', 'group')
        .prefetch_related('replies__author'),
        id=discussion_id,
        group__slug=slug
    )

    membership = get_membership(request.user, discussion.group)

    context = {
        'group': discussion.group,
        'discussion': discussion,
        'replies': discussion.replies.select_related('author'),
        'is_member': bool(membership),
        'reply_form': DiscussionReplyForm() if membership else None,
    }
    return render(request, 'groups/discussion_detail.html', context)


# -------------------- Reply --------------------
@login_required
def discussion_reply(request, slug, discussion_id):
    discussion = get_object_or_404(
        GroupDiscussion, id=discussion_id, group__slug=slug
    )

    membership = get_membership(request.user, discussion.group)

    if not membership:
        messages.error(request, 'Join group to reply.')
        return redirect('groups:discussion_detail', slug=slug, discussion_id=discussion_id)

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
                message=f'{request.user.username} replied to "{discussion.title}"',
                link=reverse('groups:discussion_detail', kwargs={
                    'slug': slug,
                    'discussion_id': discussion_id
                })
            )

        messages.success(request, 'Reply added.')

    return redirect('groups:discussion_detail', slug=slug, discussion_id=discussion_id)
