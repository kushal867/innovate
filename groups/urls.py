from django.urls import path
from . import views

app_name = 'groups'

urlpatterns = [
    # ----------- Group Core -----------
    path('', views.group_list, name='list'),
    path('create/', views.group_create, name='create'),

    # ----------- Group Actions -----------
    path('<slug:slug>/', views.group_detail, name='detail'),
    path('<slug:slug>/edit/', views.group_edit, name='edit'),
    path('<slug:slug>/delete/', views.group_delete, name='delete'),

    # ----------- Membership -----------
    path('<slug:slug>/join/', views.group_join, name='join'),
    path('<slug:slug>/leave/', views.group_leave, name='leave'),

    # ----------- Discussions -----------
    path('<slug:slug>/discussions/', views.discussion_list, name='discussion_list'),
    path('<slug:slug>/discussions/create/', views.discussion_create, name='discussion_create'),
    path('<slug:slug>/discussions/<int:discussion_id>/', views.discussion_detail, name='discussion_detail'),

    # ----------- Replies -----------
    path('<slug:slug>/discussions/<int:discussion_id>/reply/', views.discussion_reply, name='discussion_reply'),
]
