from django.urls import path

from .views import LoginAssistantView

urlpatterns = [
    path('login/', LoginAssistantView.as_view(), name='login-assistant'),
    
]
