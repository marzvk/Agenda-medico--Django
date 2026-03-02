from agenda.models import Turno, Slot
from datetime import timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone


class TurnoService:

    #  CREAR TURNO DESDE SLOT
    @staticmethod
    @transaction.atomic
    def crear_turno(slot_id, paciente):
        try:
            slot = Slot.objects.select_for_update().get(id=slot_id)
        except Slot.DoesNotExist:
            raise ValidationError("El slot no existe")

        if not slot.disponible:
            raise ValidationError("El slot no esta disponible")

        turno = Turno.objects.create(slot=slot, paciente=paciente)

        slot.disponible = False
        turno.save()

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
        pass
