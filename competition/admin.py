from django.contrib import admin
from .models import Task, Test, Solution, SolutionTestResult, Configuration


admin.site.register(Task)
admin.site.register(Test)
admin.site.register(Solution)
admin.site.register(SolutionTestResult)

@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
  def has_add_permission(self, *args, **kwargs):
    return not Configuration.objects.exists()
