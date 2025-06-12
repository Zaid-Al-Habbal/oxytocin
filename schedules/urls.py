from django.urls import path

from .views import *

urlpatterns = [
    path("weekdays/", ListWeekDaysSchedulesView.as_view(), name="list-weekdays-schedules"),

]
