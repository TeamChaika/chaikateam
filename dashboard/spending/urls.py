from django.urls import path

from . import views


urlpatterns = [
    path('', views.SpendingView.as_view())
]
