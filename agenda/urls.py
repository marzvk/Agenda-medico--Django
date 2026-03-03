from django.urls import path
from .views import turnos_views as views

app_name = "agenda"

urlpatterns = [
    path("", views.index, name="index"),
    path("slots/", views.lista_slots, name="lista_slots"),
    path("reservar/<int:slot_id>/", views.reservar_turno, name="reservar_turno"),
    path("turnos/", views.lista_turnos, name="lista_turnos"),
    path("cancelar/<int:turno_id>/", views.cancelar_turno, name="cancelar_turno"),
]
