from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ContactMessage


class ContactMessageForm(forms.ModelForm):
    """Contact Us Message Form"""

    class Meta:
        model = ContactMessage
        fields = ['name', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter your name'),
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('09xxxxxxxxx'),
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Subject of your message'),
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Write your message here'),
                'rows': 4,
            }),
        }

        labels = {
            'name': _('Name'),
            'phone': _('Phone number'),
            'subject': _('Subject'),
            'message': _('Message'),
        }
