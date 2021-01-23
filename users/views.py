from django.shortcuts import render, redirect
from django.contrib.auth.models import User

from .forms import TeamForm, ParticipantForm
from .models import Participant, Team
from competition.models import Configuration

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
        are_forms_valid = __are_forms_valid(
            team_form, participant_forms, team_members)
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
                participant_forms[i].add_error(
                    'email', 'Ten email jest już używany przez innego członka zespołu')
                return False
            team_members_emails.append(member_email)
    return True


def __is_any_team_slot_available():
    limit = Configuration.objects.all()[0].participants_limit
    teams_total = Team.objects.all().count()
    return teams_total < limit


def __save_team(team_form):
    team_user = User.objects.create(
        username=__generate_username(), password=team_form.cleaned_data['password'])
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