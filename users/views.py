from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.urls import reverse
from .forms import UserRegistrationForm, UserLoginForm, ProfileSettingsForm
from notifications.models import Notification

User = get_user_model()


def register(request):
    """Handle user registration with username, email, password, and role selection."""
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('ideas:list')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(
                    request, 
                    f'Account created successfully for {user.username}! Please log in.'
                )
                return redirect('users:login')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.capitalize()}: {error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """Handle user login with email or username and optional 'remember me' functionality."""
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('ideas:list')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        
        # Get username/email and password from POST data
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')
        
        # Validate that required fields are provided
        if not username_or_email or not password:
            messages.error(request, 'Please provide both username/email and password.')
        else:
            # Try to authenticate with username or email
            user = None
            
            # Check if input is an email
            if '@' in username_or_email:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            else:
                # Try to authenticate with username directly
                user = authenticate(request, username=username_or_email, password=password)
            
            if user is not None:
                login(request, user)
                
                # Handle 'remember me' functionality
                if not remember_me:
                    # Session expires when browser closes
                    request.session.set_expiry(0)
                else:
                    # Session lasts for 2 weeks
                    request.session.set_expiry(1209600)  # 2 weeks in seconds
                
                messages.success(request, f'Welcome back, {user.username}!')
                
                # Redirect to next page if provided, otherwise to ideas list
                next_page = request.GET.get('next', 'ideas:list')
                return redirect(next_page)
            else:
                messages.error(request, 'Invalid username/email or password. Please try again.')
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout and redirect to home page."""
    username = request.user.username
    logout(request)
    messages.success(request, f'You have been logged out successfully. See you soon, {username}!')
    return redirect('home')


def profile(request, username):
    """Display user profile with info, followers, following, and posted ideas."""
    user = get_object_or_404(User, username=username)
    
    is_following = False
    if request.user.is_authenticated:
        is_following = user.followers.filter(id=request.user.id).exists()
    
    followers_count = user.followers.count()
    following_count = user.following.count()
    
    user_ideas = user.ideas.all().order_by('-created_at')
    
    context = {
        'profile_user': user,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'user_ideas': user_ideas,
        'is_own_profile': request.user.is_authenticated and request.user.username == username,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def settings(request):
    """Handle profile settings editing for logged-in users."""
    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('users:profile', username=request.user.username)
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.capitalize()}: {error}')
    else:
        form = ProfileSettingsForm(instance=request.user)
    
    return render(request, 'users/settings.html', {'form': form})


@login_required
def follow_user(request, username):
    """Toggle follow status for a user and create notification."""
    if request.user.username == username:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'You cannot follow yourself'}, status=400)
        messages.error(request, 'You cannot follow yourself.')
        return redirect('users:profile', username=username)
    
    user_to_follow = get_object_or_404(User, username=username)
    
    is_following = user_to_follow.followers.filter(id=request.user.id).exists()
    
    if is_following:
        user_to_follow.followers.remove(request.user)
        action = 'unfollowed'
        is_now_following = False
    else:
        user_to_follow.followers.add(request.user)
        action = 'followed'
        is_now_following = True
        
        Notification.objects.create(
            recipient=user_to_follow,
            sender=request.user,
            notification_type='follow',
            title='New Follower',
            message=f'{request.user.username} started following you',
            link=reverse('users:profile', kwargs={'username': request.user.username})
        )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'action': action,
            'is_following': is_now_following,
            'followers_count': user_to_follow.followers.count()
        })
    
    messages.success(request, f'You have {action} {username}!')
    return redirect('users:profile', username=username)
