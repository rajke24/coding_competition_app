from django.shortcuts import redirect


def team_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.groups.filter(name='team').exists():
            return view_func(request, *args, **kwargs)
        return redirect('home')

    return wrapper_func


def judge_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.groups.filter(name='judge').exists():
            return view_func(request, *args, **kwargs)
        return redirect('home')

    return wrapper_func


def authorized_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        return redirect('home')

    return wrapper_func
