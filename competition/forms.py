from django import forms
from .models import Configuration

class ConfigPanelForm(forms.Form):
    competition_status = forms.BooleanField(required=False)
    ranking_visibility = forms.BooleanField(required=False)