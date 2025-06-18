from django.urls import path

from .views import *

urlpatterns = [
    path("weekdays/", ListWeekDaysSchedulesView.as_view(), name="list-weekdays-schedules"),
    path("weekdays/<int:pk>/", ShowWeekDaySchedulesView.as_view(), name="retrieve-weekday-schedules"),
    path("weekdays/<int:schedule_id>/available-hours/", ReplaceAvailableHoursView.as_view(), name="replace-available-hours-to-weekday"),
    path("weekdays/<int:schedule_id>/unavailable/", MarkWeekdayUnavailableView.as_view(), name="mark-weekday-unavailable"),
    
    path("delete-working-hour/", DeleteWorkingHourView.as_view(), name="delete-working-hour"),

]
