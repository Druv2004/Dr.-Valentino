from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))  # honeypot

    class Meta:
        model = ContactMessage
        fields = ["first_name", "last_name", "email", "topic", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 6})}
        labels = {"first_name": "First name", "last_name": "Last name", "email": "Email address", "topic": "Subject"}

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam check failed.")
        return ""
