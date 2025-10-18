from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from .models import Message
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Type your message...',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
        }
        labels = {
            'content': '',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('content'),
            Submit('submit', 'Send Message', css_class='bg-primary text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition duration-200')
        )

class ComposeMessageForm(forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
        }),
        label='Send to'
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Type your message...',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
        }),
        label='Message'
    )
    
    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user:
            self.fields['recipient'].queryset = User.objects.exclude(id=current_user.id)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('recipient'),
            Field('content'),
            Submit('submit', 'Send Message', css_class='w-full bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200')
        )
