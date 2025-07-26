from django.urls import path

from favorites import views


urlpatterns = [
    path(
        "",
        views.FavoriteListCreateView.as_view(),
        name="favorite-list-create",
    ),
    path(
        "<int:pk>/",
        views.FavoriteDestroyView.as_view(),
        name="favorite-destroy",
    ),
]
