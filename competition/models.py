

from django.db import models


# Create your models here.
from users.models import Team


class Task(models.Model):
    description = models.CharField(max_length=1000)


class Test(models.Model):
    input = models.CharField(max_length=500)
    output = models.CharField(max_length=500)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)


class Solution(models.Model):
    class SolutionStatus(models.IntegerChoices):
        NOT_EVALUATED = 1, 'Nieocenione'
        CORRECT = 2, 'Poprawne'
        INCORRECT = 3, 'Niepoprawne'
        PRESENTATION_ERROR = 4, 'Błąd prezentacji'
        COMPILATION_ERROR = 5, 'Błąd kompilacji'
        RUNTIME_ERROR = 6, 'Błąd czasu wykonania'
        TIME_EXCEEDED_ERROR = 7, 'Przekroczono czas wykonania'

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    content = models.CharField(max_length=2048)
    upload_time = models.DateTimeField(auto_now_add=True)
    solution_status = models.IntegerField(choices=SolutionStatus.choices, default=SolutionStatus.NOT_EVALUATED)


class SolutionTestResult(models.Model):
    did_pass = models.BooleanField()
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)


class Configuration(models.Model):
    class CompetitionStatus(models.IntegerChoices):
        INACTIVE = 0
        ACTIVE = 1

    class RankingVisibility(models.IntegerChoices):
        INVISIBLE = 0
        VISIBLE = 1

    participants_limit = models.PositiveIntegerField()
    competition_status = models.IntegerField(choices=CompetitionStatus.choices, default=CompetitionStatus.INACTIVE)
    ranking_visibility = models.IntegerField(choices=RankingVisibility.choices, default=RankingVisibility.VISIBLE)
