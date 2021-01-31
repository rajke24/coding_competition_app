from competition.models import Task, Solution, Test
from users.models import Team

import datetime

from django.utils import timezone

from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
from django.urls import reverse

from competition.models import Configuration


class TestViewSendSolution(TestCase):

    def setUp(self):
        self.client = Client()
        self.send_solution_url = reverse('send-solution', args=[1])

        self.team_username = "kalisz1"
        self.team_password = "123456789"
        self.configuration = Configuration.objects.create(participants_limit=50)
        team_group = Group.objects.create(name="team")

        team_user = User.objects.create_user(username=self.team_username, password=self.team_password)
        team_user.groups.add(team_group)
        team_user.save()

        team = Team.objects.create(
            team_as_user=team_user,
            guardian_first_name="Jan",
            guardian_last_name="Kowalski",
            school_name="Liceum Ogólnokształcące im. Mikołaja Kopernika w kaliszu",
            school_city="Kalisz"
        )
        team.save()

        self.judge_username = "sedzia1"
        self.judge_password = "123456"
        judge_user = User.objects.create_user(username=self.judge_username, password=self.judge_password)
        judge_group = Group.objects.create(name="judge")
        judge_user.groups.add(judge_group)

        self.task1 = Task.objects.create(
            description='FizzBuzz. W pierwszej linijce n, potem w nowych linijkach n liczb całkowitych [1, 1000]. Wypisz Fizz jeżeli liczba dzieli się przez 3, Buzz jeśli dzieli się przez 5 , FizzBuzz jeśli liczba dzieli się i przez 3 i przez 5 oraz wypisz tę liczbę jeśli liczba nie dzieli się ani przez 3 ani przez 5.'
        )

        Test.objects.create(task=self.task1, input=r'4\n3\n5\n15\n2',
                            output=r'Fizz\nBuzz\nFizzBuzz\n2'),
        Test.objects.create(task=self.task1, input=r'5\n2\n4\n8\n19\n22', output=r'2\n4\n8\n19\n22'),
        Test.objects.create(task=self.task1, input=r'4\n3\n6\n9\n12',
                            output=r'Fizz\nFizz\nFizz\nFizz'),
        Test.objects.create(task=self.task1, input=r'1\n30', output=r'FizzBuzz'),
        Test.objects.create(task=self.task1, input=r'3\n20\n60\n33',
                            output=r'Buzz\nFizzBuzz\nFizz')

    def test_send_solution_GET_user_unauthenticated(self):
        response = self.client.get(self.send_solution_url, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'competition/home.html')

    def test_send_solution_GET_team_authenticated(self):
        logged_team = self.client.login(username=self.team_username, password=self.team_password)
        response = self.client.get(self.send_solution_url, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'competition/send_solution.html')

    def test_send_solution_GET_judge_authenticated(self):
        self.client.login(username=self.judge_username, password=self.judge_password)
        response = self.client.get(self.send_solution_url, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'competition/home.html')

    def test_send_solution_POST_user_unauthenticated(self):
        response = self.client.post(self.send_solution_url, {
            "solution": "Expample solution"
        })

        self.assertEqual(response.status_code, 302)
        self.assertEquals(0, Solution.objects.all().count())

    def test_send_solution_POST_team_authenticated_and_competition_status_active(self):
        self.configuration.competition_status = Configuration.CompetitionStatus.ACTIVE
        self.configuration.save()

        logged_team = self.client.login(
            username=self.team_username,
            password=self.team_password
        )
        response = self.client.post(self.send_solution_url, {
            "solution": "Expample solution"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEquals(1, Solution.objects.all().count())

    def test_send_solution_POST_team_authenticated_and_competition_status_inactive(self):
        logged_team = self.client.login(
            username=self.team_username,
            password=self.team_password
        )
        response = self.client.post(self.send_solution_url, {
            "solution": "Expample solution"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEquals(0, Solution.objects.all().count())

    def test_send_solution_POST_judge_authenticated(self):
        logged_judge = self.client.login(
            username=self.judge_username,
            password=self.judge_password
        )
        response = self.client.post(self.send_solution_url, {
            "solution": "Expample solution"
        })

        self.assertEqual(response.status_code, 302)
        self.assertEquals(0, Solution.objects.all().count())

    def test_send_solution_POST_team_authenticated_and_correct_solution(self):
        self.configuration.competition_status = Configuration.CompetitionStatus.ACTIVE
        self.configuration.save()
        logged_team = self.client.login(
            username=self.team_username,
            password=self.team_password
        )
        response = self.client.post(self.send_solution_url, {
            "solution": """n = int(input())
for i in range(n):
    number = int(input())
    if number % 15 == 0:
        print('FizzBuzz')
    elif number % 5 == 0:
        print('Buzz')
    elif number % 3 == 0:
        print('Fizz')
    else:
        print(number)"""
        })

        self.assertEqual(response.status_code, 200)
        self.assertEquals(1, Solution.objects.all().count())
        self.assertEquals(Solution.SolutionStatus.CORRECT, Solution.objects.all()[0].solution_status)

    def test_send_solution_POST_team_authenticated_and_wrong_solution(self):
        self.configuration.competition_status = Configuration.CompetitionStatus.ACTIVE
        self.configuration.save()
        logged_team = self.client.login(
            username=self.team_username,
            password=self.team_password
        )
        response = self.client.post(self.send_solution_url, {
            "solution": "print(5)"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEquals(1, Solution.objects.all().count())
        self.assertEquals(Solution.SolutionStatus.INCORRECT, Solution.objects.all()[0].solution_status)

    def test_send_solution_POST_team_authenticated_and_presentation_error(self):
        self.configuration.competition_status = Configuration.CompetitionStatus.ACTIVE
        self.configuration.save()
        logged_team = self.client.login(
            username=self.team_username,
            password=self.team_password
        )
        response = self.client.post(self.send_solution_url, {
            "solution": """n = int(input())
for i in range(n):
    number = int(input())
    if number % 15 == 0:
        print('FizzBuzz', end='')
    elif number % 5 == 0:
        print('Buzz')
    elif number % 3 == 0:
        print('Fizz')
    else:
        print(number)"""
        })

        self.assertEqual(response.status_code, 200)
        self.assertEquals(1, Solution.objects.all().count())
        self.assertEquals(Solution.SolutionStatus.PRESENTATION_ERROR,
                          Solution.objects.all()[0].solution_status)

    def test_send_solution_POST_team_authenticated_and_compilation_error(self):
        self.configuration.competition_status = Configuration.CompetitionStatus.ACTIVE
        self.configuration.save()
        logged_team = self.client.login(
            username=self.team_username,
            password=self.team_password
        )
        response = self.client.post(self.send_solution_url, {
            "solution": "for in range(5)"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEquals(1, Solution.objects.all().count())
        self.assertEquals(Solution.SolutionStatus.COMPILATION_ERROR,
                          Solution.objects.all()[0].solution_status)

    def test_send_solution_POST_team_authenticated_and_runtime_error(self):
        self.configuration.competition_status = Configuration.CompetitionStatus.ACTIVE
        self.configuration.save()
        logged_team = self.client.login(
            username=self.team_username,
            password=self.team_password
        )
        response = self.client.post(self.send_solution_url, {
            "solution": "aaa"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEquals(1, Solution.objects.all().count())
        self.assertEquals(Solution.SolutionStatus.RUNTIME_ERROR,
                          Solution.objects.all()[0].solution_status)


class TestViewConfigPanel(TestCase):

    def setUp(self):
        self.client = Client()
        self.judge_username = 'example_judge'
        self.judge_password = 'example_password'
        Configuration.objects.create(participants_limit=50,
                                     ranking_visibility=Configuration.RankingVisibility.INVISIBLE,
                                     competition_status=Configuration.CompetitionStatus.INACTIVE)
        judge_user = User.objects.create_user(username=self.judge_username, password=self.judge_password)
        judge_group = Group.objects.create(name='judge')
        judge_user.groups.add(judge_group)
        judge_user.save()

        self.team_username = 'example_team'
        self.team_password = 'example_team_password'
        team_user = User.objects.create_user(username=self.team_username, password=self.team_password)
        team_group = Group.objects.create(name='team')
        team_user.groups.add(team_group)
        self.config_panel_url_get = '/config-panel'
        self.config_panel_url_post = '/config-panel/'
        self.config_panel_template = 'competition/configpanel.html'
        self.home_template = 'competition/home.html'
        self.configuration = Configuration.objects.all()[0]

    def test_GET_not_logged_in(self):
        response = self.client.get(self.config_panel_url_get, follow=True)
        self.assertTemplateUsed(response, self.home_template)

    def test_GET_logged_in_as_team(self):
        self.client.login(username=self.team_username, password=self.team_password)
        response = self.client.get(self.config_panel_url_get, follow=True)
        self.assertTemplateUsed(response, self.home_template)

    def test_GET_logged_in_as_judge(self):
        self.client.login(username=self.judge_username, password=self.judge_password)
        response = self.client.get(self.config_panel_url_get, follow=True)
        self.assertTemplateUsed(response, self.config_panel_template)

    def test_POST_not_logged_in(self):
        response = self.client.post(self.config_panel_url_get, {
            'competition_status': 'on',
            'ranking_visibility': 'on'
        })
        configuration = Configuration.objects.all()[0]
        self.assertEqual(self.configuration.competition_status, Configuration.CompetitionStatus.INACTIVE)
        self.assertEqual(configuration.ranking_visibility, Configuration.RankingVisibility.INVISIBLE)

    def test_POST_logged_in_as_team(self):
        self.client.login(username=self.team_username, password=self.team_password)
        response = self.client.post(self.config_panel_url_get, {
            'competition_status': 'on',
            'ranking_visibility': 'on'
        })
        configuration = Configuration.objects.all()[0]
        self.assertEqual(configuration.competition_status, Configuration.CompetitionStatus.INACTIVE)
        self.assertEqual(configuration.ranking_visibility, Configuration.RankingVisibility.INVISIBLE)

    def test_POST_logged_in_as_judge(self):
        self.client.login(username=self.judge_username, password=self.judge_password)
        response = self.client.post(self.config_panel_url_post, {
            'competition_status': 'on',
            'ranking_visibility': 'on'
        })
        configuration = Configuration.objects.all()[0]
        self.assertEqual(configuration.competition_status, Configuration.CompetitionStatus.ACTIVE)
        self.assertEqual(configuration.ranking_visibility, Configuration.RankingVisibility.VISIBLE)

    def test_POST_activate_competition(self):
        self.client.login(username=self.judge_username, password=self.judge_password)
        response = self.client.post(self.config_panel_url_post, {
            'competition_status': 'on'
        })
        configuration = Configuration.objects.all()[0]
        self.assertEqual(configuration.competition_status, Configuration.CompetitionStatus.ACTIVE)
        self.assertIsNotNone(configuration.competition_start_time)

    def test_POST_pause_competition(self):
        self.configuration.competition_status = Configuration.CompetitionStatus.ACTIVE
        self.configuration.competition_start_time = timezone.now()
        self.configuration.save()

        self.client.login(username=self.judge_username, password=self.judge_password)
        response = self.client.post(self.config_panel_url_post)

        configuration = Configuration.objects.all()[0]
        self.assertEqual(configuration.competition_status, Configuration.CompetitionStatus.INACTIVE)
        self.assertIsNotNone(configuration.competition_pause_time)

    def test_POST_resume_competition(self):
        time_now = timezone.now()
        self.configuration.competition_start_time = time_now - datetime.timedelta(minutes=30)
        self.configuration.competition_pause_time = time_now - datetime.timedelta(minutes=20)
        self.configuration.save()

        self.client.login(username=self.judge_username, password=self.judge_password)
        response = self.client.post(self.config_panel_url_post, {
            'competition_status': 'on'
        })

        configuration = Configuration.objects.all()[0]
        self.assertEqual(configuration.competition_status, Configuration.CompetitionStatus.ACTIVE)
        self.assertEqual(configuration.total_pause_time_in_minutes, 20)

    def test_POST_disable_ranking_visiblity(self):
        self.configuration.ranking_visibility = Configuration.RankingVisibility.VISIBLE
        self.configuration.save()

        self.client.login(username=self.judge_username, password=self.judge_password)
        response = self.client.post(self.config_panel_url_post)

        configuration = Configuration.objects.all()[0]
        self.assertEqual(configuration.competition_status, configuration.RankingVisibility.INVISIBLE)
        self.assertIsNotNone(configuration.ranking_visibility_change_time)

    def test_POST_enable_ranking_visibility(self):
        self.client.login(username=self.judge_username, password=self.judge_password)
        response = self.client.post(self.config_panel_url_post, {
            'ranking_visibility': 'on'
        })

        configuration = Configuration.objects.all()[0]
        self.assertEqual(configuration.ranking_visibility, configuration.RankingVisibility.VISIBLE)
