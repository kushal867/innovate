from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('compose/', views.compose, name='compose'),
    path('send/', views.send_message, name='send_message'),
    path('start/<str:username>/', views.start_conversation, name='start_conversation'),
]
