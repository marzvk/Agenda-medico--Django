from django.test import TestCase
from django.contrib.auth.models import User
from django_celery_beat.models import PeriodicTask
import datetime

from agenda.models import Medico


class SignalsMedicoTestCase(TestCase):
    """
    No necesitamos pacientes ni turnos, solo médicos.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="dr_signal_test", password="test1234"
        )
        self.medico = Medico.objects.create(
            user=self.user,
            nombre="Carlos",
            apellido="García",
            dni="11111111",
            fecha_nacimiento=datetime.date(1980, 1, 1),
            telefono="3735000000",
            email="medico_signal@test.com",
            especialidad="Kinesiología",
            matricula="MAT001",
            inicio_jornada=datetime.time(8, 0),
            fin_jornada=datetime.time(18, 0),
            tiempo_consulta=30,
            notificaciones_activas=True,
            hora_resumen_diario=datetime.time(8, 0),
            horas_recordatorio_paciente=24,
        )


class TestSignalCreacionMedico(SignalsMedicoTestCase):

    def test_crear_medico_registra_tarea_en_beat(self):
        """
        Cuando se crea un médico, la signal post_save
        tiene que registrar automáticamente su tarea
        periódica en Beat.
        """
        existe = PeriodicTask.objects.filter(
            name=f"resumen_diario_medico_{self.medico.id}"
        ).exists()

        self.assertTrue(existe)

    def test_tarea_apunta_a_la_funcion_correcta(self):
        """
        La tarea registrada tiene que apuntar
        a la función de Celery correcta, no a otra.
        """
        tarea = PeriodicTask.objects.get(name=f"resumen_diario_medico_{self.medico.id}")

        self.assertEqual(tarea.task, "agenda.notifications.tasks.tarea_resumen_diario")

    def test_tarea_habilitada_si_notificaciones_activas(self):
        """
        Si el médico tiene notificaciones activas,
        la tarea en Beat tiene que estar habilitada.
        """
        tarea = PeriodicTask.objects.get(name=f"resumen_diario_medico_{self.medico.id}")

        self.assertTrue(tarea.enabled)

    def test_tarea_deshabilitada_si_notificaciones_inactivas(self):
        """
        Si el médico tiene notificaciones desactivadas,
        la tarea en Beat tiene que estar deshabilitada.
        Beat la ignora aunque exista en la base de datos.
        """
        medico_sin_notif = Medico.objects.create(
            nombre="Sin",
            apellido="Notificaciones",
            dni="22222222",
            fecha_nacimiento=datetime.date(1985, 1, 1),
            telefono="3735000001",
            email="sin_notif@test.com",
            especialidad="Clínica",
            matricula="MAT002",
            inicio_jornada=datetime.time(8, 0),
            fin_jornada=datetime.time(18, 0),
            tiempo_consulta=30,
            notificaciones_activas=False,
            hora_resumen_diario=datetime.time(8, 0),
            horas_recordatorio_paciente=24,
        )

        tarea = PeriodicTask.objects.get(
            name=f"resumen_diario_medico_{medico_sin_notif.id}"
        )

        self.assertFalse(tarea.enabled)


class TestSignalModificacionMedico(SignalsMedicoTestCase):

    def test_cambiar_hora_resumen_actualiza_beat(self):
        """
        Si la secretaria cambia la hora del resumen diario,
        Beat tiene que reflejar el nuevo horario.
        """
        self.medico.hora_resumen_diario = datetime.time(9, 30)
        self.medico.save()

        tarea = PeriodicTask.objects.get(name=f"resumen_diario_medico_{self.medico.id}")

        self.assertEqual(tarea.crontab.hour, "9")
        self.assertEqual(tarea.crontab.minute, "30")

    def test_desactivar_notificaciones_deshabilita_tarea(self):
        """
        Si se apagan las notificaciones del médico,
        la tarea en Beat se deshabilita automáticamente.
        """
        self.medico.notificaciones_activas = False
        self.medico.save()

        tarea = PeriodicTask.objects.get(name=f"resumen_diario_medico_{self.medico.id}")

        self.assertFalse(tarea.enabled)


class TestSignalEliminacionMedico(SignalsMedicoTestCase):

    def test_borrar_medico_elimina_tarea_de_beat(self):
        """
        Cuando se borra un médico, su tarea periódica
        tiene que desaparecer de Beat.
        Sin esto quedan tareas huérfanas que intentan
        ejecutarse para un médico que no existe.
        """
        medico_id = self.medico.id
        self.medico.delete()

        existe = PeriodicTask.objects.filter(
            name=f"resumen_diario_medico_{medico_id}"
        ).exists()

        self.assertFalse(existe)
