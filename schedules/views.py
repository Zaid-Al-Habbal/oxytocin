from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from assistants.permissions import IsAssistantWithClinic
from .serializers import ListWeekDaysSchedulesSerializer
from .models import ClinicSchedule

class ListWeekDaysSchedulesView(ListAPIView):
    serializer_class = ListWeekDaysSchedulesSerializer
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]
    
    def get_queryset(self):
        user = self.request.user
        clinic = user.assistant.clinic
        return ClinicSchedule.objects.filter(clinic=clinic).prefetch_related('available_hours')
    