from django import forms

from .models import DerbyName


class NameForm(forms.ModelForm):
    name = forms.CharField(label="Name", max_length=100)
    cleared = forms.BooleanField(label="Cleared", required=False)
    archived = forms.BooleanField(label="Archived", required=False)

    class Meta:
        model = DerbyName
        fields = ("name", "cleared", "archived")
