from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils import timezone

from competition.models import Task, Solution, Configuration
from competition.views import __get_team_tasks as get_team_tasks
from users.models import Team


class TestFunctionGetTeamTasks(TestCase):

    def setUp(self):
        self.client = Client()
        self.team_username = 'example_team'
        self.team_password = 'exampel_password'
        team_user = User.objects.create_user(username=self.team_username, password=self.team_password)
        self.team = Team.objects.create(team_as_user=team_user, school_name='Przykładowa szkoła',
                                        school_city='PrzykładoweMiasto')
        self.tasks = [
            Task.objects.create(description='Przykładowe zadanie 1'),
            Task.objects.create(description='Przykładowe zadanie 2'),
            Task.objects.create(description='Przykładowe zadanie 3'),
            Task.objects.create(description='Przykładowe zadanie 4'),
            Task.objects.create(description='Przykładowe zadanie 5')
        ]

    def test_no_finished_tasks(self):
        tasks_with_statuses, are_all_finished = get_team_tasks(self.team)

        for count, task_with_status in enumerate(tasks_with_statuses):
            self.assertEquals(task_with_status['task'], self.tasks[count])
            self.assertFalse(task_with_status['is_finished'])
        self.assertFalse(are_all_finished)

    def test_some_finished_tasks(self):
        for count, task in enumerate(self.tasks):
            solution_status = Solution.SolutionStatus.CORRECT if count % 2 == 0 else Solution.SolutionStatus.PRESENTATION_ERROR
            Solution.objects.create(team=self.team, task=task, content='Przykładowe rozwiązanie',
                                    upload_time=timezone.now(), solution_status=solution_status)

        tasks_with_statuses, are_all_finished = get_team_tasks(self.team)
        for count, task_with_status in enumerate(tasks_with_statuses):
            self.assertEquals(task_with_status['task'], self.tasks[count])
            if count % 2 == 0:
                self.assertTrue(task_with_status['is_finished'])
            else:
                self.assertFalse(task_with_status['is_finished'])
        self.assertFalse(are_all_finished)

    def test_all_finished_tasks(self):
        for task in self.tasks:
            Solution.objects.create(team=self.team, task=task, content='Przykładowe rozwiązanie',
                                    upload_time=timezone.now(), solution_status=Solution.SolutionStatus.CORRECT)

        tasks_with_statuses, are_all_finished = get_team_tasks(self.team)

        for count, task_with_status in enumerate(tasks_with_statuses):
            self.assertEquals(task_with_status['task'], self.tasks[count])
            self.assertTrue(task_with_status['is_finished'])
        self.assertTrue(are_all_finished)

    def test_tasks_with_invalid_answers(self):
        for task in self.tasks:
            Solution.objects.create(team=self.team, task=task, content='Przykładowe rozwiązanie',
                                    upload_time=timezone.now(), solution_status=Solution.SolutionStatus.INCORRECT)

        tasks_with_statuses, are_all_finished = get_team_tasks(self.team)

        for count, task_with_status in enumerate(tasks_with_statuses):
            self.assertEquals(task_with_status['task'], self.tasks[count])
            self.assertFalse(task_with_status['is_finished'])
        self.assertFalse(are_all_finished)
