from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('', views.resource_list, name='list'),
    path('upload/', views.upload_resource, name='upload'),
    path('<int:pk>/', views.resource_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_resource, name='edit'),
    path('<int:pk>/delete/', views.delete_resource, name='delete'),
    path('<int:pk>/rate/', views.rate_resource, name='rate'),
    path('<int:pk>/download/', views.download_resource, name='download'),
]
