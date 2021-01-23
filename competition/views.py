import subprocess
from os import path
import os

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect
from competition.forms import ParticipantForm, TeamForm, ConfigPanelForm, SolutionForm
import random
from enum import Enum
from competition.models import Configuration, Task, Test, Solution, SolutionTestResult
from users.models import Team, Participant


def configpanel(request):
    configuration = Configuration.objects.all()[0]
    if request.method == 'POST':
        form = ConfigPanelForm(request.POST)
        if form.is_valid():
            competition_status = form.cleaned_data['competition_status']
            ranking_visibility = form.cleaned_data['ranking_visibility']
            print(competition_status)
            print(ranking_visibility)
            configuration = Configuration.objects.all()[0]
            configuration.competition_status = competition_status
            configuration.ranking_visibility = ranking_visibility
            configuration.save()
            return redirect('config-panel')
    else:
        form = ConfigPanelForm()

    return render(request, 'competition/configpanel.html', {"configuration": configuration})


def no_team_slots_available(request):
    if __is_any_team_slot_available():
        return redirect('registration')
    return render(request, 'competition/team_limit.html')


def registration_successful(request, team):
    return render(request, 'competition/registration_success.html', context={
        'team': team, 'team_members': Participant.objects.all().filter(team=team)
    })


def register(request):
    if not __is_any_team_slot_available():
        return redirect('register-no-team-slots-available')
    if request.method == 'POST':
        team_members = int(request.POST['participants_spinner'])
        team_form = TeamForm(request.POST, prefix='team')
        participant_forms = [
            ParticipantForm(request.POST, prefix='participant_1'),
            ParticipantForm(request.POST, prefix='participant_2'),
            ParticipantForm(request.POST, prefix='participant_3')
        ]
        are_forms_valid = __are_forms_valid(team_form, participant_forms, team_members)
        if are_forms_valid:
            if __is_any_team_slot_available():
                team = __save_team(team_form)
                __save_participants(participant_forms, team_members, team)
                return registration_successful(request, team)
            else:
                return redirect('register-no-team-slots-available')
        else:
            # jeżeli któraś z form jest niepoprawna, zwracamy je z powrotem żeby wyświetliły się błędy
            # odtwarzamy na nowo formy participantów które były zdisablowane na froncie, bo inaczej będą one oznaczone jako błędnie wypełnione
            __recreate_empty_forms(participant_forms, team_members)
            return render(request, 'competition/registration.html',
                          {'participants': participant_forms,
                           'team': team_form,
                           })
    else:
        team = TeamForm(prefix='team')
        participant_1 = ParticipantForm(prefix='participant_1')
        participant_2 = ParticipantForm(prefix='participant_2')
        participant_3 = ParticipantForm(prefix='participant_3')
        return render(request, 'competition/registration.html',
                      {'participants': [participant_1, participant_2, participant_3],
                       'team': team})


def __are_forms_valid(team_form, participant_forms, team_members):
    if not team_form or not team_form.is_valid():
        return False
    team_members_emails = []
    for i in range(team_members):
        if not participant_forms[i] or not participant_forms[i].is_valid():
            return False
        else:
            member_email = participant_forms[i].cleaned_data['email']
            if member_email in team_members_emails:
                participant_forms[i].add_error('email', 'Ten email jest już używany przez innego członka zespołu')
                return False
            team_members_emails.append(member_email)
    return True


def __is_any_team_slot_available():
    limit = Configuration.objects.all()[0].participants_limit
    teams_total = Team.objects.all().count()
    return teams_total < limit


def __save_team(team_form):
    team_user = User.objects.create(username=__generate_username(), password=team_form.cleaned_data['password'])
    team = team_form.save(commit=False)
    team.team_as_user = team_user
    team.save()
    return team


def __generate_username():
    return "team{0}".format(Team.objects.all().count() + 1)


def __is_username_free(username):
    return not User.objects.filter(username__exact=username).exists()


def __save_participants(participant_forms, team_members, team):
    for i in range(team_members):
        participant = participant_forms[i].save(commit=False)
        participant.team = team
        participant.save()


def __recreate_empty_forms(participant_forms, team_members):
    for i in range(team_members, 3):
        participant_forms[i] = ParticipantForm(prefix="participant_".format(i))


def send_solution(request):
    if request.method == 'POST':
        task = Task.objects.all()[0]  # placeholder
        team = Team.objects.all()[0]  # placeholder

        solution = Solution.objects.create(task=task, team=team,
                                           content=__sanitize_solution_content(request.POST['solution']))
        solution_filename = __save_solution_to_file(solution)
        solution_status = __run_tests(solution_filename, task, solution)
        __delete_solution_file(solution_filename)
        solution.solution_status = solution_status
        solution.save()
        return HttpResponse(solution_status.name)
    return render(request, 'competition/send_solution.html', context={'solution_form': SolutionForm()})


def __sanitize_solution_content(content):
    return '\n'.join(content.splitlines())


def __save_solution_to_file(solution):
    filename = __generate_filename()
    file = open(filename, 'w')
    file.write(solution.content)
    file.close()
    return filename


def __generate_filename():
    file_suffix = random.randint(1, 1000)
    while True:
        filename = "user_script{0}.py".format(file_suffix)
        if not path.exists(filename):
            return filename
        file_suffix += 1


def __run_tests(solution_script_path, task, solution):
    tests = Test.objects.all().filter(task=task)
    test_results = []
    for test in tests:
        test_result = __run_test(solution_script_path, test.input, test.output)
        did_pass = test_result == TestResult.OKAY
        SolutionTestResult.objects.create(solution=solution, test=test, did_pass=did_pass)
        test_results.append(test_result)

    for test_result in test_results:
        if test_result is TestResult.TIME_EXCEEDED_ERROR:
            return Solution.SolutionStatus.TIME_EXCEEDED_ERROR
        elif test_result is TestResult.RUNTIME_ERROR:
            return Solution.SolutionStatus.RUNTIME_ERROR
        elif test_result is TestResult.COMPILATION_ERROR:
            return Solution.SolutionStatus.COMPILATION_ERROR
        elif test_result is TestResult.PRESENTATION_ERROR:
            return Solution.SolutionStatus.PRESENTATION_ERROR
        elif test_result is TestResult.WRONG_ANSWER:
            return Solution.SolutionStatus.INCORRECT
    return Solution.SolutionStatus.CORRECT


def __run_test(script_path, test_input, test_output):
    test_input_sanitized = test_input.replace('\\n', '\n')
    test_output_sanitized = test_output.replace('\\n', '\n')
    try:
        result = subprocess.run(['python', script_path], input=test_input_sanitized, capture_output=True,
                                encoding='utf-8', check=True)
        is_output_correct = (test_output_sanitized == result.stdout.rstrip())
        if is_output_correct:
            return TestResult.OKAY
        if __is_presentation_error(result.stdout, test_output_sanitized):
            return TestResult.PRESENTATION_ERROR
        return TestResult.WRONG_ANSWER
    except subprocess.CalledProcessError as err:
        return __evaluate_error(err.stderr)


def __is_presentation_error(actual_output, expected_output):
    actual_output_stripped = "".join(actual_output.split())
    expected_output_stripped = "".join(expected_output.split())
    return actual_output_stripped == expected_output_stripped


def __evaluate_error(error_message):
    if 'SyntaxError' in error_message:
        return TestResult.COMPILATION_ERROR
    return TestResult.RUNTIME_ERROR


def __delete_solution_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)


class TestResult(Enum):
    OKAY = 1
    WRONG_ANSWER = 2
    PRESENTATION_ERROR = 3
    COMPILATION_ERROR = 4
    RUNTIME_ERROR = 5
    TIME_EXCEEDED_ERROR = 6
