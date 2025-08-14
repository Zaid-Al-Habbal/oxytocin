from django.urls import path

from financials import views


urlpatterns = [
    path(
        "",
        views.FinancialListView.as_view(),
        name="financial-list",
    ),
    path(
        "<int:pk>/",
        views.FinancialRetrieveUpdateView.as_view(),
        name="financial-retrieve-update",
    ),
]
