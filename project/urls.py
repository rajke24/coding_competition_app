from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from competition.views import configpanel, ranking
from competition import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('config-panel/', configpanel, name='config-panel'),
    path('register/', views.register, name='registration'),
    path('register/limit', views.no_team_slots_available, name='register-no-team-slots-available'),
    path('solution', views.send_solution, name='send-solution'),
    path('ranking/', ranking, name='ranking'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
