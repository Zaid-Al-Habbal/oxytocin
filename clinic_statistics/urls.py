from django.urls import path, include

from .views import *

urlpatterns = [
    path("num-of-stars/", NumOfStarsView.as_view(), name="num-of-stars"),
]
