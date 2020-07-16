from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'TTS'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^TTS/', views.TTS, name='TTS'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
