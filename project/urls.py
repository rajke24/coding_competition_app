from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from competition.views import configpanel

urlpatterns = [
    path('admin/', admin.site.urls),
    path('config-panel/', configpanel, name='config-panel')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
