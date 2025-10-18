from django.urls import path
from . import views

app_name = 'ideas'

urlpatterns = [
    path('', views.idea_list, name='list'),
    path('create/', views.idea_create, name='create'),
    path('<slug:slug>/', views.idea_detail, name='detail'),
    path('<slug:slug>/edit/', views.idea_edit, name='edit'),
    path('<slug:slug>/delete/', views.idea_delete, name='delete'),
    path('<slug:slug>/upvote/', views.idea_upvote, name='upvote'),
    path('<slug:slug>/bookmark/', views.idea_bookmark, name='bookmark'),
    path('<slug:slug>/comment/', views.add_comment, name='add_comment'),
]
