from django.urls import path
from . import views


urlpatterns = [
    path('', views.writeoffs_view),
    path('create', views.CreateWriteoffView.as_view()),
    path('<int:pk>', views.writeoff_view),
    path('<int:pk>/<str:action>', views.process_writeoff),
]
