# Generated by Django 3.1.5 on 2021-01-28 20:58
from django.db import migrations
from django.contrib.auth.hashers import make_password


def populate_database(apps, schema_editor):
    Configuration = apps.get_model('competition', 'Configuration')
    __create_configurations(Configuration)

    Task = apps.get_model('competition', 'Task')
    Test = apps.get_model('competition', 'Test')
    __create_tasks(Task, Test)

    User = apps.get_model('auth', 'User')
    Group = apps.get_model('auth', 'Group')
    Team = apps.get_model('users', 'Team')
    Participant = apps.get_model('users', 'Participant')
    __create_users(User, Group, Team, Participant)


def __create_configurations(Configuration):
    configuration = Configuration.objects.create(participants_limit=50)
    configuration.save()


def __create_tasks(Task, Test):
    task_1 = Task.objects.create(
        description='FizzBuzz. W pierwszej linijce n, potem w nowych linijkach n liczb całkowitych [1, 1000]. Wypisz Fizz jeżeli liczba dzieli się przez 3, Buzz jeśli dzieli się przez 5 , FizzBuzz jeśli liczba dzieli się i przez 3 i przez 5 oraz wypisz tę liczbę jeśli liczba nie dzieli się ani przez 3 ani przez 5.')
    tests_1 = [
        Test.objects.create(task=task_1, input=r'4\n3\n5\n15\n2', output=r'Fizz\nBuzz\nFizzBuzz\n2'),
        Test.objects.create(task=task_1, input=r'5\n2\n4\n8\n19\n22', output=r'2\n4\n8\n19\n22'),
        Test.objects.create(task=task_1, input=r'4\n3\n6\n9\n12', output=r'Fizz\nFizz\nFizz\nFizz'),
        Test.objects.create(task=task_1, input=r'1\n30', output=r'FizzBuzz'),
        Test.objects.create(task=task_1, input=r'3\n20\n60\n33', output=r'Buzz\nFizzBuzz\nFizz')
    ]
    task_2 = Task.objects.create(
        description="Napisz program, który wyznacza liczbę pierwiastków rzeczywistych równania kwadratowego. Wejście: trzy liczby rzeczywiste oznaczające współczynniki A, B i C równania kwadratowego (gdzie A != 0). Na wyjściu: liczba całkowita równa liczbie pierwiastkó rzeczywistych wczytanego równania"
    )
    tests_2 = [
        Test.objects.create(task=task_2, input=r'0.3\n0.3\n0.4', output=r'0'),
        Test.objects.create(task=task_2, input=r'0.5\n1\n0.5', output=r'0'),
        Test.objects.create(task=task_2, input=r'-0.5\n-0.5\n0')
    ]


def __create_users(User, Group, Team, Participant):
    __create_admins(Group, User)
    __create_judges(Group, User)
    __create_teams(Group, User, Team, Participant)


def __create_admins(Group, User):
    admin_group = Group.objects.create(name='admin')

    admin = User.objects.create(username='admin1', email='zbigniew.noga#xample.com', first_name='Zbigniew',
                                last_name='Noga',
                                password=make_password('haslo123'), is_staff=True, is_superuser=True)
    admin.groups.add(admin_group)
    admin.save()


def __create_judges(Group, User):
    judge_group = Group.objects.create(name='judge')
    judge = User.objects.create(username='sedzia1', email='anna.nowak@example.com', first_name='Anna',
                                last_name='Nowak',
                                password=make_password('haslo123'))
    judge.groups.add(judge_group)
    judge.save()


def __create_teams(Group, User, Team, Participant):
    team_group = Group.objects.create(name='team')

    team_1 = __create_team(Team, User, team_group, username='team1', password='haslo123', guardian_first_name='Adam',
                           guardian_last_name='Kowalski',
                           school_name='II Liceum Ogólnokształcące im. Adama Mickiewicza w Konikowie')

    team_1_participants = [
        __create_participant(Participant, team=team_1, email='grzegorz.lis@example.com', first_name='Grzegorz',
                             last_name='Lis', age=15),
        __create_participant(Participant, team=team_1, email='jolanta.sowa@example.com', first_name='Jolanta',
                             last_name='Sowa', age=16),
        __create_participant(Participant, team=team_1, email='malgorzata.kruk@example.com', first_name='Małgorzata',
                             last_name='Kruk', age=15)
    ]

    team_2 = __create_team(Team, User, team_group, username='team2', password='haslo123', guardian_first_name='Weronika',
                           guardian_last_name='Wino',
                           school_name='IV Liceum Ogólnokształcące im. Mikołaja Kopernika w Słoneczkowie')

    team_2_participants = [
        Participant.objects.create(email='jerzy.las@example.com', first_name='Jerzy', last_name='Las', age=14,
                                   team=team_2)
    ]

    team_3 = __create_team(Team, User, team_group, username='team3', password='haslo123', guardian_first_name='Michał',
                           guardian_last_name='Rogal',
                           school_name='I Liceum Ogólnokształcące im. Juliusza Słowackiego w Zygmuntowie')

    team_3_participants = [
        __create_participant(Participant, team=team_3, email='zuzanna.szpak@example.com', first_name='Zuzanna',
                             last_name='Szpak', age=15),
        __create_participant(Participant, team=team_3, email='grazyna.kot@example.com', first_name='Grazyna',
                             last_name='Kot', age=16)

    ]


def __create_team(Team, User, team_group, username, password, guardian_first_name, guardian_last_name, school_name):
    team_user = User.objects.create(username=username, password=make_password(password))
    team_user.groups.add(team_group)
    team_user.save()
    team = Team.objects.create(team_as_user=team_user, guardian_first_name=guardian_first_name,
                               guardian_last_name=guardian_last_name, school_name=school_name)
    return team


def __create_participant(Participant, team, email, first_name, last_name, age):
    return Participant.objects.create(team=team, email=email, first_name=first_name, last_name=last_name, age=age)


class Migration(migrations.Migration):
    dependencies = [
        ('competition', '0003_add_ranking_visibility_time_change'),
    ]

    operations = [
        migrations.RunPython(populate_database)
    ]