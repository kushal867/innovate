from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.db.models import Q, Avg
from .models import Resource, ResourceRating
from .forms import ResourceForm, RatingForm
from notifications.models import Notification

def resource_list(request):
    resources = Resource.objects.all()
    
    # Filter by resource type
    resource_type = request.GET.get('type', '')
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    
    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        resources = resources.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(resources, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'resource_type': resource_type,
        'search_query': search_query,
        'resource_types': Resource.RESOURCE_TYPE_CHOICES,
    }
    return render(request, 'resources/list.html', context)

@login_required
def upload_resource(request):
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()
            messages.success(request, 'Resource uploaded successfully!')
            return redirect('resources:detail', pk=resource.pk)
    else:
        form = ResourceForm()
    
    return render(request, 'resources/upload.html', {'form': form})

def resource_detail(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    ratings = resource.ratings.all()[:5]
    
    # Check if user has already rated
    user_rating = None
    if request.user.is_authenticated:
        user_rating = resource.ratings.filter(user=request.user).first()
    
    rating_form = RatingForm() if request.user.is_authenticated and not user_rating else None
    
    context = {
        'resource': resource,
        'ratings': ratings,
        'user_rating': user_rating,
        'rating_form': rating_form,
    }
    return render(request, 'resources/detail.html', context)

@login_required
def edit_resource(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    
    # Check if user is the owner
    if resource.uploaded_by != request.user:
        messages.error(request, 'You can only edit your own resources.')
        return redirect('resources:detail', pk=pk)
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resource updated successfully!')
            return redirect('resources:detail', pk=pk)
    else:
        form = ResourceForm(instance=resource)
    
    return render(request, 'resources/edit.html', {'form': form, 'resource': resource})

@login_required
def delete_resource(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    
    # Check if user is the owner
    if resource.uploaded_by != request.user:
        messages.error(request, 'You can only delete your own resources.')
        return redirect('resources:detail', pk=pk)
    
    if request.method == 'POST':
        resource.delete()
        messages.success(request, 'Resource deleted successfully!')
        return redirect('resources:list')
    
    return render(request, 'resources/delete_confirm.html', {'resource': resource})

@login_required
def rate_resource(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    
    # Check if user has already rated
    existing_rating = resource.ratings.filter(user=request.user).first()
    if existing_rating:
        messages.warning(request, 'You have already rated this resource.')
        return redirect('resources:detail', pk=pk)
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.resource = resource
            rating.user = request.user
            rating.save()
            
            # Create notification for the uploader
            if resource.uploaded_by != request.user:
                Notification.objects.create(
                    recipient=resource.uploaded_by,
                    sender=request.user,
                    notification_type='upvote',
                    title='New Rating on Your Resource',
                    message=f'{request.user.username} rated your resource "{resource.title}" with {rating.rating} stars.',
                    link=f'/resources/{resource.pk}/'
                )
            
            messages.success(request, 'Thank you for rating this resource!')
            return redirect('resources:detail', pk=pk)
    else:
        return redirect('resources:detail', pk=pk)

def download_resource(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    
    # Increment download count
    resource.download_count += 1
    resource.save()
    
    # If it's a link, redirect to it
    if resource.link:
        return redirect(resource.link)
    
    # If it's a file, serve it
    if resource.file:
        try:
            return FileResponse(resource.file.open('rb'), as_attachment=True, filename=resource.file.name.split('/')[-1])
        except FileNotFoundError:
            raise Http404("File not found")
    
    messages.error(request, 'No file or link available for this resource.')
    return redirect('resources:detail', pk=pk)
