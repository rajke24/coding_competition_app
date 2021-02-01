import datetime
from time import sleep

from django.contrib.auth.models import User, Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone
from selenium import webdriver
from seleniumlogin import force_login
from webdriver_manager.chrome import ChromeDriverManager

from competition.models import Configuration, Solution, Task
from users.models import Team


def login(user, driver, live_url):
    force_login(user, driver, live_url)
    driver.get(live_url)


def find_element_by_text(driver, text):
    return driver.find_element_by_xpath("//*[contains(text(), '{}')]".format(text))


def get_ranking_entries(driver, team_usernames):
    to_return = []
    for team_username in team_usernames:
        team_row = driver.find_element_by_id(team_username)
        team_row_children = team_row.find_elements_by_xpath("./child::*")
        team_tasks_solved = team_row_children[2]
        team_time = team_row_children[3]
        ranking_position = team_row_children[0]
        to_return.append(
            {'team_username': team_username, 'ranking_position': ranking_position.text,
             'tasks_solved': team_tasks_solved.text, 'time': team_time.text})
    return to_return


def get_ranking_entries_in_order(driver):
    to_return = []
    table_body = driver.find_element_by_id('ranking').find_elements_by_xpath("./child::*")[1]
    for table_row in table_body.find_elements_by_xpath("./child::tr"):
        record = {}
        for count, element in enumerate(table_row.find_elements_by_xpath("./child::*")):
            if count == 0:
                record['ranking_position'] = element.text
            elif count == 1:
                record['team_username'] = element.text
            elif count == 2:
                record['tasks_solved'] = element.text
            elif count == 3:
                record['time'] = element.text
        to_return.append(record)
    return to_return


def enter_ranking(driver):
    check_ranking_button = find_element_by_text(driver, 'Sprawdź ranking')
    check_ranking_button.click()


def set_up_example_data(teams, time_now, configuration):
    configuration.competition_start_time = time_now - datetime.timedelta(minutes=120)

    tasks = [
        Task.objects.create(id=1, description='Przykladowe zadanie 1'),
        Task.objects.create(id=2, description='Przykladowe zadanie 2'),
        Task.objects.create(id=3, description='Przykladowe zadanie 3'),
    ]

    Solution.objects.create(team=teams[0], task=tasks[0], content='Przykladowa zawartosc',
                            upload_time=time_now - datetime.timedelta(minutes=100),
                            solution_status=Solution.SolutionStatus.CORRECT)

    Solution.objects.create(team=teams[0], task=tasks[1], content='Przykladowa zawartosc',
                            upload_time=time_now - datetime.timedelta(minutes=80),
                            solution_status=Solution.SolutionStatus.INCORRECT)

    Solution.objects.create(team=teams[1], task=tasks[0], content='Przykladowa zawartosc',
                            upload_time=time_now - datetime.timedelta(minutes=70),
                            solution_status=Solution.SolutionStatus.CORRECT)
    Solution.objects.create(team=teams[1], task=tasks[1], content='Przykladowa zawartosc',
                            upload_time=time_now - datetime.timedelta(minutes=40),
                            solution_status=Solution.SolutionStatus.CORRECT)
    Solution.objects.create(team=teams[1], task=tasks[2], content='Przykladowa zawartosc',
                            upload_time=time_now - datetime.timedelta(minutes=10),
                            solution_status=Solution.SolutionStatus.CORRECT)

    Solution.objects.create(team=teams[2], task=tasks[0], content='Przykladowa zawartosc',
                            upload_time=time_now - datetime.timedelta(minutes=100),
                            solution_status=Solution.SolutionStatus.INCORRECT)


class RankingTest(StaticLiveServerTestCase):

    def setUp(self):
        Configuration.objects.create(participants_limit=50)
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.password = 'example_password'
        self.judge_username = 'example_judge'
        self.judge = User.objects.create_user(username=self.judge_username, password=self.password)
        judge_group = Group.objects.create(name='judge')
        self.judge.groups.add(judge_group)
        self.judge.save()
        self.team_usernames = [
            'example_team1',
            'example_team2',
            'example_team3'
        ]
        self.team_users = [User.objects.create_user(username=username, password=self.password) for username in
                           self.team_usernames]

        self.teams = [Team.objects.create(team_as_user=team_user, school_name='Przykladowa szkola',
                                          school_city='PrzykladoweMiasto') for team_user in self.team_users]
        team_group = Group.objects.create(name='team')
        for team_user in self.team_users:
            team_user.groups.add(team_group)
            team_user.save()

    def test_no_solutions(self):
        self.assertEqual(Solution.objects.count(), 0)
        login(self.team_users[0], self.driver, self.live_server_url)
        enter_ranking(self.driver)
        ranking_entries = get_ranking_entries(self.driver, self.team_usernames)
        for ranking_entry in ranking_entries:
            self.assertEqual(ranking_entry['tasks_solved'], '0')
            self.assertEqual(ranking_entry['time'], '0:00')

    def test_highlighting_team(self):
        self.assertEqual(Solution.objects.count(), 0)
        login(self.team_users[1], self.driver, self.live_server_url)
        enter_ranking(self.driver)
        highlighted_row = self.driver.find_element_by_class_name('active-team ')
        self.assertEqual(highlighted_row.get_attribute('id'), self.team_usernames[1])

    def test_calculate_ranking(self):
        configuration = Configuration.objects.all()[0]
        set_up_example_data(self.teams, timezone.now(), configuration)
        configuration.save()
        login(self.team_users[0], self.driver, self.live_server_url)
        enter_ranking(self.driver)
        ranking_entries = get_ranking_entries(self.driver, self.team_usernames)
        for ranking_entry in ranking_entries:
            if ranking_entry['team_username'] == self.team_usernames[0]:
                self.assertEqual(ranking_entry['tasks_solved'], '1')
                self.assertEqual(ranking_entry['time'], '0:40')
                self.assertEqual(ranking_entry['ranking_position'], '2')
            elif ranking_entry['team_username'] == self.team_usernames[1]:
                self.assertEqual(ranking_entry['tasks_solved'], '3')
                self.assertEqual(ranking_entry['time'], '1:50')
                self.assertEqual(ranking_entry['ranking_position'], '1')
            elif ranking_entry['team_username'] == self.team_usernames[2]:
                self.assertEqual(ranking_entry['tasks_solved'], '0')
                self.assertEqual(ranking_entry['time'], '0:20')
                self.assertEqual(ranking_entry['ranking_position'], '3')
            else:
                self.assertTrue(False)  # this shouldn't happen

    def test_calculate_ranking_visibility_off_as_team(self):
        configuration = Configuration.objects.all()[0]
        time_now = timezone.now()
        configuration.ranking_visibility = Configuration.RankingVisibility.INVISIBLE
        configuration.competition_status = Configuration.CompetitionStatus.ACTIVE
        configuration.ranking_visibility_change_time = time_now - datetime.timedelta(minutes=50)
        set_up_example_data(self.teams, time_now, configuration)
        configuration.save()

        login(self.team_users[0], self.driver, self.live_server_url)
        enter_ranking(self.driver)
        ranking_entries = get_ranking_entries(self.driver, self.team_usernames)
        for ranking_entry in ranking_entries:
            if ranking_entry['team_username'] == self.team_usernames[0]:
                self.assertEqual(ranking_entry['tasks_solved'], '1')
                self.assertEqual(ranking_entry['time'], '0:40')
                self.assertEqual(ranking_entry['ranking_position'], '1')
            elif ranking_entry['team_username'] == self.team_usernames[1]:
                self.assertEqual(ranking_entry['tasks_solved'], '1')
                self.assertEqual(ranking_entry['time'], '0:50')
                self.assertEqual(ranking_entry['ranking_position'], '2')
            elif ranking_entry['team_username'] == self.team_usernames[2]:
                self.assertEqual(ranking_entry['tasks_solved'], '0')
                self.assertEqual(ranking_entry['time'], '0:20')
                self.assertEqual(ranking_entry['ranking_position'], '3')
            else:
                self.assertTrue(False)  # this shouldn't happen

        e = find_element_by_text(driver=self.driver, text='Widoczność aktualnego rankingu została wyłączona')
        self.assertIsNotNone(e)

    def test_calculate_ranking_visibility_off_as_judge(self):
        configuration = Configuration.objects.all()[0]
        time_now = timezone.now()
        configuration.ranking_visibility = Configuration.RankingVisibility.INVISIBLE
        configuration.competition_status = Configuration.CompetitionStatus.ACTIVE
        configuration.ranking_visibility_change_time = time_now - datetime.timedelta(minutes=50)
        set_up_example_data(self.teams, time_now, configuration)
        configuration.save()

        login(self.judge, self.driver, self.live_server_url)
        enter_ranking(self.driver)
        ranking_entries = get_ranking_entries(self.driver, self.team_usernames)
        for ranking_entry in ranking_entries:
            if ranking_entry['team_username'] == self.team_usernames[0]:
                self.assertEqual(ranking_entry['tasks_solved'], '1')
                self.assertEqual(ranking_entry['time'], '0:40')
                self.assertEqual(ranking_entry['ranking_position'], '2')
            elif ranking_entry['team_username'] == self.team_usernames[1]:
                self.assertEqual(ranking_entry['tasks_solved'], '3')
                self.assertEqual(ranking_entry['time'], '1:50')
                self.assertEqual(ranking_entry['ranking_position'], '1')
            elif ranking_entry['team_username'] == self.team_usernames[2]:
                self.assertEqual(ranking_entry['tasks_solved'], '0')
                self.assertEqual(ranking_entry['time'], '0:20')
                self.assertEqual(ranking_entry['ranking_position'], '3')
            else:
                self.assertTrue(False)  # this shouldn't happen

    def test_back_button(self):
        login(self.team_users[0], self.driver, self.live_server_url)
        enter_ranking(self.driver)
        sleep(0.5)
        self.driver.find_element_by_class_name('material-icons').click()
        self.assertEqual(self.live_server_url + "/", self.driver.current_url)

    def test_sort_by_ascending(self):
        configuration = Configuration.objects.all()[0]
        set_up_example_data(self.teams, timezone.now(), configuration)
        configuration.save()
        login(self.team_users[0], self.driver, self.live_server_url)
        enter_ranking(self.driver)

        sleep(0.5)
        self.driver.find_element_by_link_text('rosnąco').click()

        ranking_entries = get_ranking_entries_in_order(self.driver)

        self.assertEqual(ranking_entries[0]['team_username'], self.team_usernames[1])
        self.assertEqual(ranking_entries[0]['ranking_position'], '1')
        self.assertEqual(ranking_entries[1]['team_username'], self.team_usernames[0])
        self.assertEqual(ranking_entries[1]['ranking_position'], '2')
        self.assertEqual(ranking_entries[2]['team_username'], self.team_usernames[2])
        self.assertEqual(ranking_entries[2]['ranking_position'], '3')

    def test_sort_by_descending(self):
        configuration = Configuration.objects.all()[0]
        set_up_example_data(self.teams, timezone.now(), configuration)
        configuration.save()
        login(self.team_users[0], self.driver, self.live_server_url)
        enter_ranking(self.driver)
        sleep(0.5)
        self.driver.find_element_by_link_text('malejąco').click()
        ranking_entries = get_ranking_entries_in_order(self.driver)
        self.assertEqual(ranking_entries[0]['team_username'], self.team_usernames[2])
        self.assertEqual(ranking_entries[0]['ranking_position'], '3')
        self.assertEqual(ranking_entries[1]['team_username'], self.team_usernames[0])
        self.assertEqual(ranking_entries[1]['ranking_position'], '2')
        self.assertEqual(ranking_entries[2]['team_username'], self.team_usernames[1])
        self.assertEqual(ranking_entries[2]['ranking_position'], '1')
