from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from .models import Group, GroupDiscussion, DiscussionReply


# Reusable CSS styles
INPUT_CLASS = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
CHECKBOX_CLASS = 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
BUTTON_CLASS = 'w-full bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200'


class BaseForm(forms.ModelForm):
    """Base form to reduce repetition"""
    
    submit_label = "Submit"

    def setup_helper(self):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

    def add_submit(self, label=None, css_class=BUTTON_CLASS):
        return Submit('submit', label or self.submit_label, css_class=css_class)


# -------------------- Group Form --------------------
class GroupForm(BaseForm):
    submit_label = "Create Group"

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

        self.setup_helper()

        self.helper.layout = Layout(
            Field('name', css_class=INPUT_CLASS),
            Field('description', css_class=INPUT_CLASS),
            Field('topic', css_class=INPUT_CLASS),
            Field('is_private', css_class=CHECKBOX_CLASS),
            Field('image', css_class=INPUT_CLASS),
            self.add_submit()
        )


# -------------------- Discussion Form --------------------
class GroupDiscussionForm(BaseForm):
    submit_label = "Post Discussion"

    class Meta:
        model = GroupDiscussion
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Discussion title...'}),
            'content': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Write your discussion post...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setup_helper()

        self.helper.layout = Layout(
            Field('title', css_class=INPUT_CLASS),
            Field('content', css_class=INPUT_CLASS),
            self.add_submit()
        )


# -------------------- Reply Form --------------------
class DiscussionReplyForm(BaseForm):
    submit_label = "Post Reply"

    class Meta:
        model = DiscussionReply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Write your reply...',
                'class': INPUT_CLASS
            }),
        }
        labels = {
            'content': '',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setup_helper()

        self.helper.layout = Layout(
            Field('content'),
            self.add_submit(css_class='bg-primary text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition duration-200')
        )
