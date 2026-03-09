from django.urls import path
from .views import turnos_views as views
from agenda.views.slots_views import generar_agenda, crear_slot_manual
from .views import medico_views as medico
from .views.pacientes_views import (
    lista_pacientes,
    detalle_paciente,
    editar_paciente,
    crear_paciente,
    editar_historia,
)

app_name = "agenda"

urlpatterns = [
    path("", views.lista_turnos, name="index"),
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
        "medico/<int:medico_id>/slot-manual/",
        crear_slot_manual,
        name="crear_slot_manual",
    ),
    path(
        "medico/<int:medico_id>/agenda/",
        medico.agenda_medico,
        name="agenda_medico",
    ),
    path(
        "medico/<int:medico_id>/disponibilidad/",
        medico.gestionar_disponibilidad,
        name="gestionar_disponibilidad",
    ),
    path("pacientes/", lista_pacientes, name="lista_pacientes"),
    path("pacientes/nuevo/", crear_paciente, name="crear_paciente"),
    path("pacientes/editar/<int:pk>/", editar_paciente, name="editar_paciente"),
    path("paciente/<int:paciente_id>/", detalle_paciente, name="detalle_paciente"),
    path("paciente/<int:pk>/historia/", editar_historia, name="editar_historia"),
]
