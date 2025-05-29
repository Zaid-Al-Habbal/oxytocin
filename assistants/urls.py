from django.urls import path

from .views import LoginAssistantView, CompleteAssistantRegistrationView

urlpatterns = [
    path('login/', LoginAssistantView.as_view(), name='login-assistant'),
    path('complete-register/', CompleteAssistantRegistrationView.as_view(), name='complete-assistant-registeration'),
]
