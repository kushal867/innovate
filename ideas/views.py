from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.urls import reverse
from .models import Idea, Comment, Upvote, Bookmark, Category
from .forms import IdeaForm, CommentForm
from notifications.models import Notification

def idea_list(request):
    ideas = Idea.objects.select_related('author', 'category').prefetch_related('tags', 'upvotes', 'comments').annotate(
        upvote_count=Count('upvotes', distinct=True),
        comment_count=Count('comments', distinct=True)
    ).order_by('-created_at')
    
    category_filter = request.GET.get('category')
    if category_filter:
        ideas = ideas.filter(category__name=category_filter)
    
    search_query = request.GET.get('q')
    if search_query:
        ideas = ideas.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    paginator = Paginator(ideas, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_filter,
        'search_query': search_query,
    }
    return render(request, 'ideas/list.html', context)

@login_required
def idea_create(request):
    if request.method == 'POST':
        form = IdeaForm(request.POST)
        if form.is_valid():
            idea = form.save(commit=False)
            idea.author = request.user
            idea.save()
            form.save_m2m()
            messages.success(request, 'Your idea has been posted successfully!')
            return redirect('ideas:detail', slug=idea.slug)
    else:
        form = IdeaForm()
    
    context = {'form': form}
    return render(request, 'ideas/create.html', context)

def idea_detail(request, slug):
    idea = get_object_or_404(
        Idea.objects.select_related('author', 'category')
        .prefetch_related('tags', 'upvotes', 'comments__author', 'comments__replies__author'),
        slug=slug
    )
    
    comments = idea.comments.filter(parent__isnull=True).select_related('author').prefetch_related('replies__author')
    
    user_upvoted = False
    user_bookmarked = False
    
    if request.user.is_authenticated:
        user_upvoted = Upvote.objects.filter(idea=idea, user=request.user).exists()
        user_bookmarked = Bookmark.objects.filter(idea=idea, user=request.user).exists()
    
    comment_form = CommentForm()
    
    context = {
        'idea': idea,
        'comments': comments,
        'comment_form': comment_form,
        'user_upvoted': user_upvoted,
        'user_bookmarked': user_bookmarked,
    }
    return render(request, 'ideas/detail.html', context)

@login_required
def idea_edit(request, slug):
    idea = get_object_or_404(Idea, slug=slug)
    
    if idea.author != request.user:
        messages.error(request, 'You can only edit your own ideas.')
        return redirect('ideas:detail', slug=slug)
    
    if request.method == 'POST':
        form = IdeaForm(request.POST, instance=idea)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your idea has been updated successfully!')
            return redirect('ideas:detail', slug=idea.slug)
    else:
        form = IdeaForm(instance=idea)
    
    context = {'form': form, 'idea': idea}
    return render(request, 'ideas/edit.html', context)

@login_required
def idea_delete(request, slug):
    idea = get_object_or_404(Idea, slug=slug)
    
    if idea.author != request.user:
        messages.error(request, 'You can only delete your own ideas.')
        return redirect('ideas:detail', slug=slug)
    
    if request.method == 'POST':
        idea.delete()
        messages.success(request, 'Your idea has been deleted successfully!')
        return redirect('ideas:list')
    
    context = {'idea': idea}
    return render(request, 'ideas/delete_confirm.html', context)

@login_required
def idea_upvote(request, slug):
    idea = get_object_or_404(Idea, slug=slug)
    
    upvote, created = Upvote.objects.get_or_create(idea=idea, user=request.user)
    
    if not created:
        upvote.delete()
        upvoted = False
    else:
        upvoted = True
        if idea.author != request.user:
            Notification.objects.create(
                recipient=idea.author,
                sender=request.user,
                notification_type='upvote',
                title='New Upvote',
                message=f'{request.user.username} upvoted your idea "{idea.title}"',
                link=reverse('ideas:detail', kwargs={'slug': idea.slug})
            )
    
    upvote_count = idea.upvotes.count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'upvoted': upvoted,
            'upvote_count': upvote_count
        })
    
    return redirect('ideas:detail', slug=slug)

@login_required
def idea_bookmark(request, slug):
    idea = get_object_or_404(Idea, slug=slug)
    
    bookmark, created = Bookmark.objects.get_or_create(idea=idea, user=request.user)
    
    if not created:
        bookmark.delete()
        bookmarked = False
        message = 'Idea removed from bookmarks.'
    else:
        bookmarked = True
        message = 'Idea bookmarked successfully!'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'bookmarked': bookmarked,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('ideas:detail', slug=slug)

@login_required
def add_comment(request, slug):
    idea = get_object_or_404(Idea, slug=slug)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.idea = idea
            comment.author = request.user
            
            parent_id = request.POST.get('parent_id')
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                comment.parent = parent_comment
            
            comment.save()
            
            if idea.author != request.user:
                Notification.objects.create(
                    recipient=idea.author,
                    sender=request.user,
                    notification_type='comment',
                    title='New Comment',
                    message=f'{request.user.username} commented on your idea "{idea.title}"',
                    link=reverse('ideas:detail', kwargs={'slug': idea.slug})
                )
            
            if parent_id and parent_comment.author != request.user:
                Notification.objects.create(
                    recipient=parent_comment.author,
                    sender=request.user,
                    notification_type='comment',
                    title='New Reply',
                    message=f'{request.user.username} replied to your comment on "{idea.title}"',
                    link=reverse('ideas:detail', kwargs={'slug': idea.slug})
                )
            
            messages.success(request, 'Your comment has been posted!')
            return redirect('ideas:detail', slug=slug)
    
    return redirect('ideas:detail', slug=slug)
