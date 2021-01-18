

from django.db import models


# Create your models here.
class Task(models.Model):
    description = models.CharField(max_length=1000)


class Test(models.Model):
    input = models.CharField(max_length=500)
    output = models.CharField(max_length=500)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)


class Solution(models.Model):
    class SolutionStatus(models.IntegerChoices):
        NOT_EVALUATED = 1
        CORRECT = 2
        INCORRECT = 3
        PRESENTATION_ERROR = 4
        COMPILATION_ERROR = 5
        RUNTIME_ERROR = 6
        TIME_EXCEEDED_ERROR = 7

    content = models.CharField(max_length=2048)
    upload_time = models.DateTimeField()
    solution_status = models.IntegerField(choices=SolutionStatus.choices)


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
    competition_status = models.IntegerField(choices=CompetitionStatus.choices)
    ranking_visibility = models.IntegerField(choices=RankingVisibility.choices)
