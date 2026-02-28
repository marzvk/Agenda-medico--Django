from agenda.models import Turno
from datetime import timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone


class TurnoService:

    @staticmethod
    @transaction.atomic
    def crear_turno(datos: dict) -> Turno:

        medico = datos["medico"]
        paciente = datos["paciente"]

        fecha_inicio = datos["fecha_hora"]
        if fecha_inicio.tzinfo is None:
            fecha_inicio = timezone.make_aware(fecha_inicio)
        duracion = datos.get("duracion_minutos", 30)

        fecha_fin = fecha_inicio + timedelta(minutes=duracion)

        TurnoService._validar_disponibilidad(medico, fecha_inicio, fecha_fin)
        TurnoService._validar_superposicion(medico, fecha_inicio, fecha_fin)

        turno = Turno.objects.create(
            medico=medico,
            paciente=paciente,
            fecha_hora=fecha_inicio,
            duracion_minutos=duracion,
        )

        TurnoService._programar_notificacion(turno)

        return turno

    @staticmethod
    def _validar_disponibilidad(medico, inicio, fin):

        dia = inicio.weekday()

        bloques = medico.disponibilidades.filter(dias_semana=dia, activo=True)

        if not bloques.exists():
            raise ValidationError("El doctor no atiende este dia.")

        for bloque in bloques:
            if inicio.time() >= bloque.hora_inicio and fin.time() <= bloque.hora_fin:
                return
            raise ValidationError("El turno esta fuera del horario del doctor.")

    @staticmethod
    def _validar_superposicion(medico, inicio, fin):

        turnos = Turno.objects.filter(
            medico=medico, estado=Turno.EstadoTurno.PROGRAMADO
        )

        for turno in turnos:
            existente_inicio = turno.fecha_hora
            existente_fin = existente_inicio + timedelta(minutes=turno.duracion_minutos)

            if existente_inicio < fin and existente_fin > inicio:
                raise ValidationError("El medico ya tiene turno en ese horario")

    @staticmethod
    def _programar_notificacion(turno):
        pass
