from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils import timezone

from competition.models import Task, Solution, Configuration
from competition.views import __get_team_tasks as get_team_tasks
from competition.views import __calculate_total_time as calculate_total_time
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


class TestCalculateTotalTime(TestCase):
    def setUp(self):
        self.team_username = "kalisz1"
        self.team_password = "123456789"
        team_user = User.objects.create_user(username=self.team_username, password=self.team_password)
        team_user.save()

        self.team = Team.objects.create(
            team_as_user=team_user,
            guardian_first_name="Jan",
            guardian_last_name="Kowalski",
            school_name="Liceum Ogólnokształcące im. Mikołaja Kopernika w kaliszu",
            school_city="Kalisz"
        )
        self.team.save()

        Configuration.objects.create(participants_limit=50, competition_start_time=timezone.now())

        self.tasks = [
            Task.objects.create(description="Zadanie 1"),
            Task.objects.create(description="Zadanie 2"),
            Task.objects.create(description="Zadanie 3"),
            Task.objects.create(description="Zadanie 4"),
            Task.objects.create(description="Zadanie 5"),
        ]


    def test_all_solutions_incorrect(self):
        for num, task in enumerate(self.tasks):
            Solution.objects.create(team=self.team, task=task, content="Rozwiązanie",
                                    upload_time=timezone.now() + timezone.timedelta(minutes=num * 10), 
                                    solution_status=Solution.SolutionStatus.INCORRECT
                                    )

        team_solutions = Solution.objects.filter(team=self.team)
        time, correct_solutions_count = calculate_total_time(team_solutions)

        self.assertEquals(0, correct_solutions_count)
        self.assertEquals(6000, time)


    def test_all_solutions_correct(self):
        for num, task in enumerate(self.tasks):
            Solution.objects.create(team=self.team, task=task, content="Rozwiązanie",
                                    upload_time=timezone.now() + timezone.timedelta(minutes=(num + 1) * 10),
                                    solution_status=Solution.SolutionStatus.CORRECT
                                    )

        team_solutions = Solution.objects.filter(team=self.team)
        time, correct_solutions_count = calculate_total_time(team_solutions)

        self.assertEquals(5, correct_solutions_count)
        self.assertEquals(3000, time)


    def test_zero_solutions(self):
        team_solutions = Solution.objects.filter(team=self.team)
        time, correct_solutions_count = calculate_total_time(team_solutions)

        self.assertEquals(0, correct_solutions_count)
        self.assertEquals(0, time)

    def test_three_correct_two_incorrect_solutions(self):
        for num, task in enumerate(self.tasks):
            if num % 2 == 0:
                Solution.objects.create(team=self.team, task=task, content="Rozwiązanie",
                                        upload_time=timezone.now() + timezone.timedelta(minutes=(num + 1) * 10),
                                        solution_status=Solution.SolutionStatus.CORRECT
                                        )
            else:
                Solution.objects.create(team=self.team, task=task, content="Rozwiązanie",
                                        upload_time=timezone.now() + timezone.timedelta(minutes=(num + 1) * 10),
                                        solution_status=Solution.SolutionStatus.INCORRECT
                                        )

        team_solutions = Solution.objects.filter(team=self.team)
        time, correct_solutions_count = calculate_total_time(team_solutions)

        self.assertEquals(3, correct_solutions_count)
        self.assertEquals(5400, time)
