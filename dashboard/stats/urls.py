from django.urls import path

from . import views

urlpatterns = [
    path('', views.total_stats_view),
    path('hungry', views.hungry_dishes_view),
    path('guests', views.guests_view),
    path('prim', views.prim_dishes_view),
]
