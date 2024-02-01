from django.urls import path
from . import views

urlpatterns = [
    path('register', views.RegisterView.as_view()),
    path('register-requests/', views.register_requests_view),
    path('register-requests/<int:pk>/confirm', views.confirm_request),
    path('register-requests/<int:pk>/deny', views.deny_request),
    path('login', views.login_view),
    path('logout', views.logout_view)
]
