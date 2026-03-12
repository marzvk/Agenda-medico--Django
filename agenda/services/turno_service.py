from agenda.models import Turno, Slot
from datetime import datetime, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone


class TurnoService:

    #  CREAR TURNO DESDE SLOT
    @staticmethod
    @transaction.atomic
    def crear_turno(slot, paciente):

        slot = Slot.objects.select_for_update().get(id=slot.id)

        if not slot.disponible:
            raise ValidationError("El slot no esta disponible")

        turno, created = Turno.objects.update_or_create(
            slot=slot,
            defaults={
                "paciente": paciente,
                "estado": Turno.EstadoTurno.PROGRAMADO,
            },
        )

        slot.disponible = False
        slot.save(update_fields=["disponible"])

        # fuera de transaction.atomic por si falla el email, sino se caeria la creacion de turno
        TurnoService._programar_notificacion(turno)

        return turno

    @staticmethod
    @transaction.atomic
    def cancelar_turno(turno):
        if turno.estado == Turno.EstadoTurno.CANCELADO:
            return turno

        turno.estado = Turno.EstadoTurno.CANCELADO
        turno.save()

        slot = turno.slot
        slot.disponible = True
        slot.save()

        return turno

    @staticmethod
    def _programar_notificacion(turno):
        """Este es el puente entre la acción de la secretaria y el sistema de notificaciones. Cuando se crea un turno, este método recibe el objeto y programa dos tareas en Celery."""

        from agenda.notifications.tasks import (
            tarea_confirmacion_turno,
            tarea_recordatorio_turno,
        )

        medico = turno.slot.medico

        if not medico.notificaciones_activas:
            return

        # ── Confirmación inmediata ──────────
        # delay : ejecutá esta tarea ahora en background
        tarea_confirmacion_turno.delay(turno.id)

        # ── Recordatorio X horas antes ──────
        fecha_hora_turno = datetime.combine(
            turno.slot.fecha,
            turno.slot.hora_inicio,
            tzinfo=timezone.get_current_timezone(),
        )

        eta_recordatorio = fecha_hora_turno - timedelta(
            hours=medico.horas_recordatorio_paciente
        )

        # solo armamos el eta para el futuro
        if eta_recordatorio > timezone.now():
            tarea_recordatorio_turno.apply_async(args=[turno.id], eta=eta_recordatorio)
        # apply_async, le dice a celery guarda esta tarea en redis, pero ejecutala en el momento indicado
