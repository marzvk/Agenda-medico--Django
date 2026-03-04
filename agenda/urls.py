from django.urls import path
from .views import turnos_views as views
from agenda.views.slots_views import generar_agenda
from .views import medico_views as medico

app_name = "agenda"

urlpatterns = [
    path("", views.index, name="index"),
    path("slots/", views.lista_slots, name="lista_slots"),
    path("reservar/<int:slot_id>/", views.reservar_turno, name="reservar_turno"),
    path("turnos/", views.lista_turnos, name="lista_turnos"),
    path(
        "turnos/<int:turno_id>/asistido/", views.marcar_asistido, name="marcar_asistido"
    ),
    path("cancelar/<int:turno_id>/", views.cancelar_turno, name="cancelar_turno"),
    path("medicos/", medico.lista_medicos, name="lista_medicos"),
    path(
        "medico/<int:medico_id>/generar-agenda/", generar_agenda, name="generar_agenda"
    ),
    path(
        "medico/<int:medico_id>/agenda/",
        medico.agenda_medico,
        name="agenda_medico",
    ),
]
