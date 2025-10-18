from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, HTML
from .models import Resource, ResourceRating

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'resource_type', 'file', 'link', 'category', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Describe this resource...'}),
            'title': forms.TextInput(attrs={'placeholder': 'Resource title...'}),
            'category': forms.TextInput(attrs={'placeholder': 'e.g., Programming, Design, Business...'}),
            'tags': forms.TextInput(attrs={'placeholder': 'Enter tags separated by commas'}),
            'link': forms.URLInput(attrs={'placeholder': 'https://example.com/resource'}),
        }
        help_texts = {
            'file': 'Upload a file (PDF, DOC, PPT, Video, Code files)',
            'link': 'Or provide an external link',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Field('title', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Field('description', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Field('resource_type', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            HTML('<div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4"><p class="text-sm text-blue-800">You can either upload a file OR provide an external link (not both).</p></div>'),
            Field('file', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Field('link', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Field('category', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Field('tags', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Submit('submit', 'Upload Resource', css_class='w-full bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        link = cleaned_data.get('link')
        
        if not file and not link:
            raise forms.ValidationError('Please provide either a file or a link.')
        
        if file and link:
            raise forms.ValidationError('Please provide either a file or a link, not both.')
        
        return cleaned_data

class RatingForm(forms.ModelForm):
    class Meta:
        model = ResourceRating
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'review': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your thoughts about this resource...',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
        }
        labels = {
            'review': 'Review (optional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('rating', css_class='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'),
            Field('review'),
            Submit('submit', 'Submit Rating', css_class='w-full bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200')
        )
