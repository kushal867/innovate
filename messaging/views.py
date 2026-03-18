from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.db.models import Max, Count, Q
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from .forms import MessageForm, ComposeMessageForm
from notifications.models import Notification

User = get_user_model()


# -------------------- Helpers --------------------
def get_or_create_conversation(user1, user2):
    conversation = Conversation.objects.filter(
        participants=user1
    ).filter(
        participants=user2
    ).first()

    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(user1, user2)

    return conversation


def send_notification(recipient, sender, conversation):
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type='message',
        title='New Message',
        message=f'{sender.username} sent you a message',
        link=f'/messages/conversation/{conversation.id}/'
    )


# -------------------- Inbox --------------------
@login_required
def inbox(request):
    conversations = (
        Conversation.objects.filter(participants=request.user)
        .annotate(last_message_time=Max('messages__created_at'))
        .order_by('-last_message_time')
        .prefetch_related('participants', 'messages')
    )

    conversation_list = []

    for conv in conversations:
        other_user = conv.get_other_participant(request.user)
        last_message = conv.messages.order_by('-created_at').first()

        unread_count = conv.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()

        conversation_list.append({
            'conversation': conv,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })

    return render(request, 'messaging/inbox.html', {
        'conversations': conversation_list
    })


# -------------------- Conversation Detail --------------------
@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in conversation.participants.all():
        django_messages.error(request, "Permission denied.")
        return redirect('messaging:inbox')

    other_user = conversation.get_other_participant(request.user)

    # Mark messages as read
    conversation.messages.filter(
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    form = MessageForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = request.user
        message.save()

        send_notification(other_user, request.user, conversation)

        return redirect('messaging:conversation_detail', conversation_id=conversation.id)

    return render(request, 'messaging/conversation.html', {
        'conversation': conversation,
        'other_user': other_user,
        'messages': conversation.messages.select_related('sender'),
        'form': form,
    })


# -------------------- Send Message (AJAX / POST) --------------------
@login_required
def send_message(request):
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')

        if not (recipient_id and content):
            return redirect('messaging:inbox')

        recipient = get_object_or_404(User, id=recipient_id)
        conversation = get_or_create_conversation(request.user, recipient)

        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )

        send_notification(recipient, request.user, conversation)

        return redirect('messaging:conversation_detail', conversation_id=conversation.id)

    return redirect('messaging:inbox')


# -------------------- Compose --------------------
@login_required
def compose(request):
    form = ComposeMessageForm(request.POST or None, current_user=request.user)

    if request.method == 'POST' and form.is_valid():
        recipient = form.cleaned_data['recipient']
        content = form.cleaned_data['content']

        conversation = get_or_create_conversation(request.user, recipient)

        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )

        send_notification(recipient, request.user, conversation)

        return redirect('messaging:conversation_detail', conversation_id=conversation.id)

    return render(request, 'messaging/compose.html', {'form': form})


# -------------------- Start Conversation --------------------
@login_required
def start_conversation(request, username):
    recipient = get_object_or_404(User, username=username)

    if recipient == request.user:
        django_messages.error(request, "You cannot message yourself.")
        return redirect('messaging:inbox')

    conversation = get_or_create_conversation(request.user, recipient)

    return redirect('messaging:conversation_detail', conversation_id=conversation.id)
