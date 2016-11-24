from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^callBack/$', views.callBack, name='callBack'),
]

# url(r'^getCache/$', views.getCache, name='getCache'),