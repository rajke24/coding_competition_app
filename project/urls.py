from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

from competition.views import configpanel, ranking, send_solution, home
from users.views import register, no_team_slots_available, login_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name="home"),
    path('config-panel/', configpanel, name='config-panel'),
    path('register/', register, name='registration'),
    path('register/limit', no_team_slots_available, name='register-no-team-slots-available'),
    path('solution', send_solution, name='send-solution'),
    path('ranking/', ranking, name='ranking'),
    path('login/', login_page, name='login'),
    path('logout/', LogoutView.as_view(template_name='users/logout.html'), name='logout'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
