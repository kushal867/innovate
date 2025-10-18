from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.db.models import Q, Max, Count, Case, When, IntegerField
from django.contrib.auth import get_user_model
from .models import Conversation, Message
from .forms import MessageForm, ComposeMessageForm
from notifications.models import Notification

User = get_user_model()

@login_required
def inbox(request):
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count(
            Case(
                When(
                    messages__is_read=False,
                    messages__sender__in=Conversation.objects.get(pk=Q(pk__in=[])).participants.exclude(id=request.user.id) if False else User.objects.exclude(id=request.user.id),
                    then=1
                ),
                output_field=IntegerField()
            )
        )
    ).order_by('-last_message_time')
    
    conversation_list = []
    for conv in conversations:
        last_message = conv.messages.last()
        other_user = conv.get_other_participant(request.user)
        unread_count = conv.messages.filter(is_read=False).exclude(sender=request.user).count()
        
        conversation_list.append({
            'conversation': conv,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })
    
    context = {
        'conversations': conversation_list,
    }
    return render(request, 'messaging/inbox.html', context)

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    if request.user not in conversation.participants.all():
        django_messages.error(request, "You don't have permission to view this conversation.")
        return redirect('messaging:inbox')
    
    other_user = conversation.get_other_participant(request.user)
    
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            
            Notification.objects.create(
                recipient=other_user,
                sender=request.user,
                notification_type='message',
                title='New Message',
                message=f'{request.user.username} sent you a message',
                link=f'/messages/conversation/{conversation.id}/'
            )
            
            django_messages.success(request, 'Message sent successfully!')
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    messages_list = conversation.messages.all()
    
    context = {
        'conversation': conversation,
        'other_user': other_user,
        'messages': messages_list,
        'form': form,
    }
    return render(request, 'messaging/conversation.html', context)

@login_required
def send_message(request):
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')
        
        if recipient_id and content:
            recipient = get_object_or_404(User, id=recipient_id)
            
            conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=recipient
            ).first()
            
            if not conversation:
                conversation = Conversation.objects.create()
                conversation.participants.add(request.user, recipient)
            
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
            Notification.objects.create(
                recipient=recipient,
                sender=request.user,
                notification_type='message',
                title='New Message',
                message=f'{request.user.username} sent you a message',
                link=f'/messages/conversation/{conversation.id}/'
            )
            
            django_messages.success(request, 'Message sent successfully!')
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    
    return redirect('messaging:inbox')

@login_required
def compose(request):
    if request.method == 'POST':
        form = ComposeMessageForm(request.POST, current_user=request.user)
        if form.is_valid():
            recipient = form.cleaned_data['recipient']
            content = form.cleaned_data['content']
            
            conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=recipient
            ).first()
            
            if not conversation:
                conversation = Conversation.objects.create()
                conversation.participants.add(request.user, recipient)
            
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
            Notification.objects.create(
                recipient=recipient,
                sender=request.user,
                notification_type='message',
                title='New Message',
                message=f'{request.user.username} sent you a message',
                link=f'/messages/conversation/{conversation.id}/'
            )
            
            django_messages.success(request, 'Message sent successfully!')
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        form = ComposeMessageForm(current_user=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'messaging/compose.html', context)

@login_required
def start_conversation(request, username):
    recipient = get_object_or_404(User, username=username)
    
    if recipient == request.user:
        django_messages.error(request, "You cannot message yourself.")
        return redirect('messaging:inbox')
    
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=recipient
    ).first()
    
    if conversation:
        return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, recipient)
        return redirect('messaging:conversation_detail', conversation_id=conversation.id)
