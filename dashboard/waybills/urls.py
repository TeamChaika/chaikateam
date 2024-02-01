from django.urls import path
from . import views


urlpatterns = [
    path('', views.waybills_view('all')),
    path('create', views.CreateWaybillView.as_view()),
    path('<int:pk>', views.waybill_view),
    path('<int:pk>/edit', views.EditWaybillView.as_view()),
    path('<int:pk>/<str:action>', views.process_waybill),
    path('incoming', views.waybills_view('incoming')),
    path('outgoing', views.waybills_view('outgoing')),
]
