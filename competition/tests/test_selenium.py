import datetime
from time import sleep

from django.contrib.auth.models import User, Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone
from selenium import webdriver
from seleniumlogin import force_login
from webdriver_manager.chrome import ChromeDriverManager
from django.urls import reverse
from django.contrib.auth.models import User, Group
from users.models import Team
from django.utils import timezone
from selenium.webdriver.support.ui import Select
from competition.models import Configuration, Solution, Task, Test


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
    table_body = driver.find_element_by_id(
        'ranking').find_elements_by_xpath("./child::*")[1]
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
    configuration.competition_start_time = time_now - \
        datetime.timedelta(minutes=120)

    tasks = [
        Task.objects.create(id=1, description='Przykladowe zadanie 1'),
        Task.objects.create(id=2, description='Przykladowe zadanie 2'),
        Task.objects.create(id=3, description='Przykladowe zadanie 3'),
    ]

    Solution.objects.create(team=teams[0], task=tasks[0], content='Przykladowa zawartosc',
                            upload_time=time_now -
                            datetime.timedelta(minutes=100),
                            solution_status=Solution.SolutionStatus.CORRECT)

    Solution.objects.create(team=teams[0], task=tasks[1], content='Przykladowa zawartosc',
                            upload_time=time_now -
                            datetime.timedelta(minutes=80),
                            solution_status=Solution.SolutionStatus.INCORRECT)

    Solution.objects.create(team=teams[1], task=tasks[0], content='Przykladowa zawartosc',
                            upload_time=time_now -
                            datetime.timedelta(minutes=70),
                            solution_status=Solution.SolutionStatus.CORRECT)
    Solution.objects.create(team=teams[1], task=tasks[1], content='Przykladowa zawartosc',
                            upload_time=time_now -
                            datetime.timedelta(minutes=40),
                            solution_status=Solution.SolutionStatus.CORRECT)
    Solution.objects.create(team=teams[1], task=tasks[2], content='Przykladowa zawartosc',
                            upload_time=time_now -
                            datetime.timedelta(minutes=10),
                            solution_status=Solution.SolutionStatus.CORRECT)

    Solution.objects.create(team=teams[2], task=tasks[0], content='Przykladowa zawartosc',
                            upload_time=time_now -
                            datetime.timedelta(minutes=100),
                            solution_status=Solution.SolutionStatus.INCORRECT)


class RankingTest(StaticLiveServerTestCase):

    def setUp(self):
        Configuration.objects.create(participants_limit=50)
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.password = 'example_password'
        self.judge_username = 'example_judge'
        self.judge = User.objects.create_user(
            username=self.judge_username, password=self.password)
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
        highlighted_row = self.driver.find_element_by_class_name(
            'active-team ')
        self.assertEqual(highlighted_row.get_attribute(
            'id'), self.team_usernames[1])

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
        configuration.ranking_visibility_change_time = time_now - \
            datetime.timedelta(minutes=50)
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

        e = find_element_by_text(
            driver=self.driver, text='Widoczność aktualnego rankingu została wyłączona')
        self.assertIsNotNone(e)

    def test_calculate_ranking_visibility_off_as_judge(self):
        configuration = Configuration.objects.all()[0]
        time_now = timezone.now()
        configuration.ranking_visibility = Configuration.RankingVisibility.INVISIBLE
        configuration.competition_status = Configuration.CompetitionStatus.ACTIVE
        configuration.ranking_visibility_change_time = time_now - \
            datetime.timedelta(minutes=50)
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

        self.assertEqual(
            ranking_entries[0]['team_username'], self.team_usernames[1])
        self.assertEqual(ranking_entries[0]['ranking_position'], '1')
        self.assertEqual(
            ranking_entries[1]['team_username'], self.team_usernames[0])
        self.assertEqual(ranking_entries[1]['ranking_position'], '2')
        self.assertEqual(
            ranking_entries[2]['team_username'], self.team_usernames[2])
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
        self.assertEqual(
            ranking_entries[0]['team_username'], self.team_usernames[2])
        self.assertEqual(ranking_entries[0]['ranking_position'], '3')
        self.assertEqual(
            ranking_entries[1]['team_username'], self.team_usernames[0])
        self.assertEqual(ranking_entries[1]['ranking_position'], '2')
        self.assertEqual(
            ranking_entries[2]['team_username'], self.team_usernames[1])
        self.assertEqual(ranking_entries[2]['ranking_position'], '1')


############################
# SEND SOLUTION PAGE TESTS #
############################

def go_to_task_panel(driver, task_num):
    select = Select(driver.find_element_by_name('tasks'))
    select.select_by_value(str(task_num))
    find_element_by_text(driver, 'Przejdź do zadania').click()


def click_button_on_confirmation_modal(driver, btn_text):
    confirmation_modal = driver.find_element_by_class_name('confirmation-modal')
    btn = find_element_by_text(driver, btn_text)
    btn.click()

def set_competition_status_active(configuration):
    configuration.competition_status = Configuration.CompetitionStatus.ACTIVE
    configuration.save()


def fill_in_solution_textarea(driver, solution_content):
    textarea = driver.find_element_by_id('id_solution')
    textarea.send_keys(solution_content)


class TestSendSolutionPage(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Chrome(ChromeDriverManager().install())
        self.send_solution_url = reverse('send-solution', args=[1])
        self.team_username = "kalisz1"
        self.team_password = "123456789"
        self.configuration = Configuration.objects.create(
            participants_limit=50, competition_start_time=timezone.now())

        self.team_user = User.objects.create_user(
            username=self.team_username, password=self.team_password)
        team_group = Group.objects.create(name="team")
        self.team_user.groups.add(team_group)
        self.team_user.save()

        team = Team.objects.create(
            team_as_user=self.team_user,
            guardian_first_name="Jan",
            guardian_last_name="Kowalski",
            school_name="Liceum Ogólnokształcące im. Mikołaja Kopernika w kaliszu",
            school_city="Kalisz"
        )
        team.save()

        self.task1 = Task.objects.create(id=1, description="Zadanie 1")

        Test.objects.create(task=self.task1, input=r'4\n3\n5\n15\n2',
                            output=r'Fizz\nBuzz\nFizzBuzz\n2'),
        Test.objects.create(
            task=self.task1, input=r'5\n2\n4\n8\n19\n22', output=r'2\n4\n8\n19\n22'),
        Test.objects.create(task=self.task1, input=r'4\n3\n6\n9\n12',
                            output=r'Fizz\nFizz\nFizz\nFizz'),
        Test.objects.create(task=self.task1, input=r'1\n30',
                            output=r'FizzBuzz'),
        Test.objects.create(task=self.task1, input=r'3\n20\n60\n33',
                            output=r'Buzz\nFizzBuzz\nFizz')


    def test_solution_panel_available(self):
        force_login(self.team_user, self.browser, self.live_server_url)
        self.browser.get(self.live_server_url)

        go_to_task_panel(self.browser, task_num=1)
        sleep(0.5)
        task_panel = self.browser.find_element_by_class_name('task-panel')
        self.assertEquals(
            task_panel.find_element_by_tag_name('p').text,
            self.task1.description
        )

    def test_home_button_works(self):
        force_login(self.team_user, self.browser, self.live_server_url)
        self.browser.get(self.live_server_url)

        go_to_task_panel(self.browser, task_num=1)
        sleep(0.5)
        self.browser.find_element_by_id('home-icon').click()
        sleep(0.5)
        self.assertEqual(self.live_server_url + "/", self.browser.current_url)


    def test_confirm_send_solution_pops_up(self):
        force_login(self.team_user, self.browser, self.live_server_url)
        self.browser.get(self.live_server_url)

        go_to_task_panel(self.browser, task_num=1)
        sleep(0.5)

        self.browser.find_element_by_id('send-btn').click()
        confirmation_modal = self.browser.find_element_by_class_name(
            'confirmation-modal')
        confirmation_modal_h1 = confirmation_modal.find_element_by_tag_name(
            'h1')

        self.assertIsNotNone(confirmation_modal)
        self.assertEquals(confirmation_modal_h1.text,
                          'Czy na pewno chcesz przesłać rozwiązanie ?')


    def test_cancel_send_solution_button_works(self):
        force_login(self.team_user, self.browser, self.live_server_url)
        self.browser.get(self.live_server_url)

        go_to_task_panel(self.browser, task_num=1)
        sleep(0.5)

        self.browser.find_element_by_id('send-btn').click()
        click_button_on_confirmation_modal(self.browser, 'Nie')
        self.assertEquals(
            self.browser.current_url,
            self.live_server_url + self.send_solution_url
        )


    def test_empty_solution_modal_pops_up_when_empty_solution(self):
        force_login(self.team_user, self.browser, self.live_server_url)
        self.browser.get(self.live_server_url)

        go_to_task_panel(self.browser, task_num=1)
        sleep(0.5)

        self.browser.find_element_by_id('send-btn').click()
        click_button_on_confirmation_modal(self.browser, 'Tak')

        competition_inactive_modal = self.browser.find_element_by_class_name('sending-error-modal')

        self.assertIsNotNone(competition_inactive_modal)
        self.assertEquals(
            competition_inactive_modal.find_element_by_tag_name('h1').text, 
            'Błąd przesyłania'
            )
        self.assertEquals(
            competition_inactive_modal.find_element_by_tag_name('p').text, 
            'Rozwiązanie użytkownia jest puste'
            )


    def test_competition_inactive_modal_pops_up(self):
        force_login(self.team_user, self.browser, self.live_server_url)
        self.browser.get(self.live_server_url)

        go_to_task_panel(self.browser, task_num=1)
        sleep(0.5)

        fill_in_solution_textarea(self.browser, 'print(5)')

        self.browser.find_element_by_id('send-btn').click()
        click_button_on_confirmation_modal(self.browser, 'Tak')

        competition_inactive_modal = self.browser.find_element_by_class_name('sending-error-modal')

        self.assertIsNotNone(competition_inactive_modal)
        self.assertEquals(
            competition_inactive_modal.find_element_by_tag_name('h1').text, 
            'Błąd przesyłania'
            )
        self.assertEquals(
            competition_inactive_modal.find_element_by_tag_name('p').text, 
            'Zawody są nieaktywne'
            )


    def test_incorrect_solution_modal_pops_up_when_incorrect_solution(self):
        set_competition_status_active(self.configuration)
        force_login(self.team_user, self.browser, self.live_server_url)
        self.browser.get(self.live_server_url)

        go_to_task_panel(self.browser, task_num=1)
        sleep(0.5)

        fill_in_solution_textarea(self.browser, "print(5)")

        self.browser.find_element_by_id('send-btn').click()
        click_button_on_confirmation_modal(self.browser, 'Tak')

        incorrect_solution_modal = self.browser.find_element_by_class_name('wrong-answer-modal')

        self.assertIsNotNone(incorrect_solution_modal)
        self.assertEquals(
            incorrect_solution_modal.find_element_by_tag_name('h1').text, 
            'Rozwiązanie jest niepoprawne'
            )
        self.assertEquals(
            incorrect_solution_modal.find_element_by_tag_name('p').text, 
            'Przyczyna: Niepoprawna odpowiedź'
            )
        self.assertIsNotNone(incorrect_solution_modal.find_element_by_id('clear-icon'))


    def test_correct_solution_modal_pops_up_when_correct_solution(self):
        set_competition_status_active(self.configuration)
        force_login(self.team_user, self.browser, self.live_server_url)
        self.browser.get(self.live_server_url)

        go_to_task_panel(self.browser, task_num=1)
        sleep(0.5)

        fill_in_solution_textarea(self.browser, """n = int(input())
for i in range(n):
    number = int(input())
    if number % 15 == 0:
        print('FizzBuzz')
    elif number % 5 == 0:
        print('Buzz')
    elif number % 3 == 0:
        print('Fizz')
    else:
        print(number)""")

        self.browser.find_element_by_id('send-btn').click()
        click_button_on_confirmation_modal(self.browser, 'Tak')

        correct_solution_modal = self.browser.find_element_by_class_name('correct-answer-modal')

        self.assertIsNotNone(correct_solution_modal)
        self.assertEquals(
            correct_solution_modal.find_element_by_tag_name('h1').text, 
            'Rozwiązanie jest poprawne'
            )
        self.assertIsNotNone(correct_solution_modal.find_element_by_id('check-icon'))
    
    
    def test_presentation_error_modal_pops_up_when_presentation_error(self):
        set_competition_status_active(self.configuration)
        force_login(self.team_user, self.browser, self.live_server_url)
        self.browser.get(self.live_server_url)

        go_to_task_panel(self.browser, task_num=1)
        sleep(0.5)

        fill_in_solution_textarea(self.browser, """n = int(input())
for i in range(n):
    number = int(input())
    if number % 15 == 0:
        print('FizzBuzz', end='')
    elif number % 5 == 0:
        print('Buzz')
    elif number % 3 == 0:
        print('Fizz')
    else:
        print(number)""")

        self.browser.find_element_by_id('send-btn').click()
        click_button_on_confirmation_modal(self.browser, 'Tak')

        incorrect_solution_modal = self.browser.find_element_by_class_name('wrong-answer-modal')

        self.assertIsNotNone(incorrect_solution_modal)
        self.assertEquals(
            incorrect_solution_modal.find_element_by_tag_name('h1').text,
            'Rozwiązanie jest niepoprawne'
        )
        self.assertEquals(
            incorrect_solution_modal.find_element_by_tag_name('p').text,
            'Przyczyna: Błąd prezentacji'
        )
        self.assertIsNotNone(
            incorrect_solution_modal.find_element_by_id('clear-icon'))


    def test_compilation_error_modal_pops_up_when_compilation_error(self):
        set_competition_status_active(self.configuration)
        force_login(self.team_user, self.browser, self.live_server_url)
        self.browser.get(self.live_server_url)

        go_to_task_panel(self.browser, task_num=1)
        sleep(0.5)

        fill_in_solution_textarea(self.browser, "for in range(5)")

        self.browser.find_element_by_id('send-btn').click()
        click_button_on_confirmation_modal(self.browser, 'Tak')

        incorrect_solution_modal = self.browser.find_element_by_class_name(
            'wrong-answer-modal')

        self.assertIsNotNone(incorrect_solution_modal)
        self.assertEquals(
            incorrect_solution_modal.find_element_by_tag_name('h1').text,
            'Rozwiązanie jest niepoprawne'
        )
        self.assertEquals(
            incorrect_solution_modal.find_element_by_tag_name('p').text,
            'Przyczyna: Błąd kompilacji'
        )
        self.assertIsNotNone(
            incorrect_solution_modal.find_element_by_id('clear-icon'))


    def test_runtime_error_modal_pops_up_when_runtime_error(self):
        set_competition_status_active(self.configuration)
        force_login(self.team_user, self.browser, self.live_server_url)
        self.browser.get(self.live_server_url)

        go_to_task_panel(self.browser, task_num=1)
        sleep(0.5)

        fill_in_solution_textarea(self.browser, "aaa")

        self.browser.find_element_by_id('send-btn').click()
        click_button_on_confirmation_modal(self.browser, 'Tak')

        incorrect_solution_modal = self.browser.find_element_by_class_name(
            'wrong-answer-modal')

        self.assertIsNotNone(incorrect_solution_modal)
        self.assertEquals(
            incorrect_solution_modal.find_element_by_tag_name('h1').text,
            'Rozwiązanie jest niepoprawne'
        )
        self.assertEquals(
            incorrect_solution_modal.find_element_by_tag_name('p').text,
            'Przyczyna: Błąd czasu wykonania'
        )
        self.assertIsNotNone(
            incorrect_solution_modal.find_element_by_id('clear-icon'))
