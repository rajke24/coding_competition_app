from django import forms
from .models import Configuration
from django import forms
from django.core.validators import MinLengthValidator, MaxLengthValidator

from users.models import Participant
from users.models import Team


class ConfigPanelForm(forms.Form):
    competition_status = forms.BooleanField(required=False)
    ranking_visibility = forms.BooleanField(required=False)


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        exclude = ['team', ]
        widgets = {
            'age': forms.NumberInput(attrs={'min': '1', 'max': '99'})
        }
        fields = (
            'first_name',
            'last_name',
            'email',
            'age'
        )

    def clean(self):
        cleaned_data = self.cleaned_data
        email = cleaned_data.get("email")
        if Participant.objects.filter(email=email).exists():
            self.add_error('email', 'Istnieje już uczestnik o takim emailu')
        return cleaned_data


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        exclude = ['team_as_user', 'is_disqualified']

    password = forms.CharField(widget=forms.PasswordInput(), validators=[
        MinLengthValidator(8, "Hasło musi mieć 8-20 znaków"),
        MaxLengthValidator(20, "Hasło musi mieć 8-20 znaków")
    ], label="Hasło *")
    password_confirm = forms.CharField(widget=forms.PasswordInput(), validators=[
        MinLengthValidator(8, "Hasło musi mieć 8-20 znaków"),
        MaxLengthValidator(20, "Hasło musi mieć 8-20 znaków")
    ], label="Powtórz hasło *")

    def clean(self):
        cleaned_data = self.cleaned_data
        password_data = cleaned_data.get("password")
        password_confirm_data = cleaned_data.get("password_confirm")
        if password_data != password_confirm_data:
            self.add_error('password_confirm', 'Hasła się nie zgadzają')
        return cleaned_data


class SolutionForm(forms.Form):
    solution = forms.CharField(widget=forms.Textarea)

