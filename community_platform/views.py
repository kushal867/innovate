from django.shortcuts import render
from ideas.models import Idea
from events.models import Event
from django.utils import timezone

def home(request):
    latest_ideas = Idea.objects.all()[:6]
    upcoming_events = Event.objects.filter(start_date__gte=timezone.now()).order_by('start_date')[:4]
    
    context = {
        'latest_ideas': latest_ideas,
        'upcoming_events': upcoming_events,
    }
    return render(request, 'home.html', context)
