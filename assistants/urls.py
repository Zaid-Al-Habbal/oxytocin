from django.urls import path

from .views import LoginAssistantView, CompleteAssistantRegistrationView, AssistantProfileView

urlpatterns = [
    path('login/', LoginAssistantView.as_view(), name='login-assistant'),
    path('complete-register/', CompleteAssistantRegistrationView.as_view(), name='complete-assistant-registeration'),
    path('me/', AssistantProfileView.as_view(), name='view-update-assistant-profile'),
]
