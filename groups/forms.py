from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from .models import Group, GroupDiscussion, DiscussionReply

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'topic', 'is_private', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
        }
        labels = {
            'topic': 'Category',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Field('description', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Field('topic', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Field('is_private', css_class='w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'),
            Field('image', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Submit('submit', 'Create Group', css_class='w-full bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200')
        )

class GroupDiscussionForm(forms.ModelForm):
    class Meta:
        model = GroupDiscussion
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Write your discussion post...'}),
            'title': forms.TextInput(attrs={'placeholder': 'Discussion title...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('title', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Field('content', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Submit('submit', 'Post Discussion', css_class='w-full bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200')
        )

class DiscussionReplyForm(forms.ModelForm):
    class Meta:
        model = DiscussionReply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Write your reply...',
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
            Submit('submit', 'Post Reply', css_class='bg-primary text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition duration-200')
        )
