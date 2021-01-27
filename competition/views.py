import subprocess
from os import path
import os
from datetime import datetime

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import ConfigPanelForm, SolutionForm
import random
from enum import Enum
from .models import Configuration, Task, Test, Solution, SolutionTestResult
from users.models import Team, Participant


def configpanel(request):
    configuration = Configuration.objects.all()[0]
    if request.method == 'POST':
        form = ConfigPanelForm(request.POST)
        if form.is_valid():
            competition_status = form.cleaned_data['competition_status']
            ranking_visibility = form.cleaned_data['ranking_visibility']
            configuration.competition_status = competition_status
            configuration.ranking_visibility = ranking_visibility
            if ranking_visibility == False:
                time = datetime.now().strftime("%H:%M")
                configuration.ranking_visibility_change_time = time
            configuration.save()
            return redirect('config-panel')
    else:
        form = ConfigPanelForm()

    return render(request, 'competition/configpanel.html', {"configuration": configuration})


def send_solution(request, task_id):
    #todo: check 1) user is team 2) task_id is valid id 3) team haven't done this task already

    if request.method == 'POST':
        task = Task.objects.all().filter(id=task_id).first()  # placeholder
        team = Team.objects.all().filter(team_as_user__username=request.user).first()

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


def ranking(request):
    teams = Team.objects.all()
    return render(request, 'competition/ranking.html',
                  {"teams": teams, 'configuration': Configuration.objects.all()[0]})


def home(request):
    if request.method == 'POST':
        task_id = int(request.POST['tasks'])
        return redirect('send-solution', task_id)
    else:
        context = {}
        is_user_team = request.user.groups.filter(name='team').exists()
        if is_user_team:
            team = Team.objects.all().filter(team_as_user=request.user).first()
            team_tasks, are_all_tasks_finished = __get_team_tasks(team)
            context['tasks'] = team_tasks
            context['are_all_tasks_finished'] = are_all_tasks_finished
        return render(request, 'competition/home.html', context)


def __get_team_tasks(team):
    all_tasks = Task.objects.all()
    finished_tasks = Solution.objects.all().filter(team=team).filter(
        solution_status=Solution.SolutionStatus.CORRECT).values_list('task', flat=True)
    tasks_with_statuses = []
    are_all_finished = True
    for task in all_tasks:
        is_finished = task.id in finished_tasks
        if not is_finished:
            are_all_finished = False
        tasks_with_statuses.append({'task': task, 'is_finished': is_finished})
    return tasks_with_statuses, are_all_finished
