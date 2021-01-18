from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


# Create your models here.
class Team(models.Model):
    team_as_user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Zespół-użytkownik")
    is_disqualified = models.BooleanField(default=False, verbose_name="Czy zdyskwalifkowany")
    guardian_first_name = models.CharField(max_length=64, blank=True, verbose_name="Imię opiekuna")
    guardian_last_name = models.CharField(max_length=64, blank=True, verbose_name="Nazwisko opiekuna")
    school_name = models.CharField(max_length=100, verbose_name="Nazwa szkoły")

    def __str__(self):
        return self.team_as_user.username


class Participant(models.Model):
    email = models.EmailField(primary_key=True, verbose_name="Adres e-mail")
    first_name = models.CharField(max_length=64, verbose_name="Imię")
    last_name = models.CharField(max_length=64, verbose_name="Nazwisko")
    age = models.IntegerField(verbose_name="Wiek", validators=[
        MinValueValidator(14, "Wiek musi być pomiędzy 14 a 99"),
        MaxValueValidator(99, "Wiek musi być pomiędzy 14 a 99")
    ])
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="Zespół")
