from django.urls import path

from .views import *

urlpatterns = [
    path("weekdays/", ListWeekDaysSchedulesView.as_view(), name="list-weekdays-schedules"),
    path("weekdays/<int:pk>/", ShowWeekDaySchedulesView.as_view(), name="retrieve-weekday-schedules"),
    path("weekdays/<int:schedule_id>/available-hours/", ReplaceAvailableHoursView.as_view(), name="replace-available-hours-of-weekday"),
    path("weekdays/<int:schedule_id>/mark-unavailable/", MarkWeekdayUnavailableView.as_view(), name="mark-weekday-unavailable"),
    
    path("special-dates/delete-working-hour/", DeleteWorkingHourView.as_view(), name="delete-working-hour"),
    path("special-dates/available-hours/", ReplaceAvailableHoursSpecialDatesView.as_view(), name="replace-available-hours-of-special-date"),
    path("special-dates/mark-unavailable/", MarkSpecialDateUnavailableView.as_view(), name="mark-special-date-unavailable"),

]
