# agenda/tests/test_celery_tasks.py
# Pruebas de las tareas de Celery invocadas DE FORMA SÍNCRONA (.run()).
# Evitamos Redis/broker: la lógica de cada tarea se ejecuta en el proceso.

from django.test import TestCase
from django.core import mail
from datetime import date, time

from agenda.models import Medico, Paciente, Slot, Turno
from agenda.notifications.tasks import (
    tarea_confirmacion_turno,
    tarea_recordatorio_turno,
    tarea_resumen_diario,
)


class TareasBase(TestCase):
    """Datos base para las tareas (mismos campos que email_service)."""

    def setUp(self):
        self.medico = Medico.objects.create(
            nombre="Carlos",
            apellido="García",
            dni="12345678",
            fecha_nacimiento=date(1980, 1, 1),
            telefono="3735000000",
            email="medico@test.com",
            especialidad="Kinesiología",
            matricula="MAT001",
            inicio_jornada=time(8, 0),
            fin_jornada=time(18, 0),
            tiempo_consulta=30,
            notificaciones_activas=True,
            hora_resumen_diario=time(8, 0),
            horas_recordatorio_paciente=24,
        )
        self.paciente = Paciente.objects.create(
            nombre="Juan",
            apellido="Pérez",
            dni="87654321",
            fecha_nacimiento=date(1990, 5, 15),
            telefono="3735111111",
            email="paciente@test.com",
            historia_clinica="Sin antecedentes",
            posee_obra_social=False,
            obra_social="",
        )
        self.slot = Slot.objects.create(
            medico=self.medico,
            fecha=date.today(),
            hora_inicio=time(9, 0),
            hora_fin=time(9, 30),
            disponible=False,
        )
        self.turno = Turno.objects.create(
            slot=self.slot,
            paciente=self.paciente,
            estado=Turno.EstadoTurno.PROGRAMADO,
        )


class TestTareaConfirmacionTurno(TareasBase):

    def test_turno_existente_envia_mail_al_paciente(self):
        tarea_confirmacion_turno.run(self.turno.id)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("paciente@test.com", mail.outbox[0].to)

    def test_turno_inexistente_no_crashea_ni_envia(self):
        """Un turno borrado (o nunca confirmado por el worker) no rompe la tarea."""
        tarea_confirmacion_turno.run(999999)

        self.assertEqual(len(mail.outbox), 0)


class TestTareaRecordatorioTurno(TareasBase):

    def test_turno_existente_envia_recordatorio(self):
        tarea_recordatorio_turno.run(self.turno.id)

        self.assertEqual(len(mail.outbox), 1)

    def test_turno_cancelado_no_envia(self):
        self.turno.estado = Turno.EstadoTurno.CANCELADO
        self.turno.save()

        tarea_recordatorio_turno.run(self.turno.id)

        self.assertEqual(len(mail.outbox), 0)

    def test_turno_inexistente_no_crashea(self):
        tarea_recordatorio_turno.run(999999)

        self.assertEqual(len(mail.outbox), 0)


class TestTareaResumenDiario(TareasBase):

    def test_medico_existente_recibe_resumen(self):
        tarea_resumen_diario.run(self.medico.id)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("medico@test.com", mail.outbox[0].to)

    def test_sin_turnos_avisa_igualmente(self):
        from django_celery_beat.models import PeriodicTask

        self.turno.delete()
        tarea_resumen_diario.run(self.medico.id)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("0 turnos", mail.outbox[0].subject)
        PeriodicTask.objects.filter(
            name=f"resumen_diario_medico_{self.medico.id}"
        ).delete()

    def test_medico_inexistente_no_crashea(self):
        tarea_resumen_diario.run(999999)

        self.assertEqual(len(mail.outbox), 0)