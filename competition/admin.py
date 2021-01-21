from django.contrib import admin
from .models import Task, Test, Solution, SolutionTestResult, Configuration


admin.site.register(Task)
admin.site.register(Test)
admin.site.register(Solution)
admin.site.register(SolutionTestResult)
admin.site.register(Configuration)
