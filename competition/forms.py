from django import forms
from .models import Configuration


class ConfigPanelForm(forms.Form):
    competition_status = forms.BooleanField(required=False)
    ranking_visibility = forms.BooleanField(required=False)


class SolutionForm(forms.Form):
    solution = forms.CharField(widget=forms.Textarea, label="Rozwiązanie")