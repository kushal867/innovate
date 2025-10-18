from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Div, Row, Column
from .models import Event

class EventForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
        })
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
        })
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
        })
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
        })
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type', 'location', 'is_online', 
                  'meeting_link', 'max_participants', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self.fields['start_date'].initial = self.instance.start_date.date()
            self.fields['start_time'].initial = self.instance.start_date.time()
            self.fields['end_date'].initial = self.instance.end_date.date()
            self.fields['end_time'].initial = self.instance.end_date.time()
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('title', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent', placeholder='Event title'),
            Field('description', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent', placeholder='Describe your event...'),
            Field('event_type', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-0'),
                Column('start_time', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('end_date', css_class='form-group col-md-6 mb-0'),
                Column('end_time', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Field('location', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent', placeholder='Event location or "Online"'),
            Field('is_online', css_class='w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'),
            Field('meeting_link', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent', placeholder='Meeting link (if online)'),
            Field('max_participants', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent', placeholder='Maximum number of participants (optional)'),
            Field('image', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Submit('submit', 'Create Event', css_class='w-full bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        start_time = cleaned_data.get('start_time')
        end_date = cleaned_data.get('end_date')
        end_time = cleaned_data.get('end_time')
        
        if start_date and start_time and end_date and end_time:
            from datetime import datetime
            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)
            
            if end_datetime <= start_datetime:
                raise forms.ValidationError('End date/time must be after start date/time.')
            
            cleaned_data['start_date'] = start_datetime
            cleaned_data['end_date'] = end_datetime
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.start_date = self.cleaned_data['start_date']
        instance.end_date = self.cleaned_data['end_date']
        if commit:
            instance.save()
        return instance
