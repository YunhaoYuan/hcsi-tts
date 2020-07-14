from django.conf.urls import url
from TTS import views

urlpatterns = [
    url(r'^index/$',views.index),
]