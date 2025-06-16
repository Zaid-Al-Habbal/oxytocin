from django.urls import path

from .views import *

urlpatterns = [
    path("weekdays/", ListWeekDaysSchedulesView.as_view(), name="list-weekdays-schedules"),
    path("weekdays/<int:pk>/", ShowWeekDaySchedulesView.as_view(), name="retrieve-weekday-schedules"),
    path("weekdays/<int:schedule_id>/available-hours/", AddAvailableHourView.as_view(), name="add-available-hour-to-weekday"),
    path("weekdays/<int:schedule_id>/available-hours/<int:hour_id>/", UpdateAvailableHourView.as_view(), name="update-available-hour-to-weekday"),
    

]
