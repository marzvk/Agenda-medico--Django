from django.test import TestCase
from django.core import mail
from django.utils import timezone
from django.contrib.auth.models import User
import datetime

from agenda.models import Medico, Paciente, Slot, Turno
from agenda.notifications.email_service import (
    enviar_confirmacion_turno,
    enviar_recordatorio_turno,
    enviar_resumen_diario,
)


class EmailServiceTestCase(TestCase):
    """Datos para usar en los tests"""

    def setUp(self):
        print("ejecutando setUp //////////////////////////////////////")
        self.user = User.objects.create_user(username="dr_test", password="test1234")

        self.medico = Medico.objects.create(
            user=self.user,
            nombre="Carlos",
            apellido="García",
            dni="12345678",
            fecha_nacimiento=datetime.date(1980, 1, 1),
            telefono="3735000000",
            email="medico@test.com",
            especialidad="Kinesiología",
            matricula="MAT001",
            inicio_jornada=datetime.time(8, 0),
            fin_jornada=datetime.time(18, 0),
            tiempo_consulta=30,
            notificaciones_activas=True,
            hora_resumen_diario=datetime.time(8, 0),
            horas_recordatorio_paciente=24,
        )

        self.paciente = Paciente.objects.create(
            nombre="Juan",
            apellido="Pérez",
            dni="87654321",
            fecha_nacimiento=datetime.date(1990, 5, 15),
            telefono="3735111111",
            email="paciente@test.com",
            historia_clinica="Sin antecedentes",
            posee_obra_social=False,
            obra_social="",
        )

        self.slot = Slot.objects.create(
            medico=self.medico,
            fecha=timezone.localdate(),
            hora_inicio=datetime.time(9, 0),
            hora_fin=datetime.time(9, 30),
            disponible=False,
        )

        self.turno = Turno.objects.create(
            slot=self.slot,
            paciente=self.paciente,
            estado=Turno.EstadoTurno.PROGRAMADO,
        )


# EMAIL PARA CONFIRMACION TURNO
class TestEnviarConfirmacionTurno(EmailServiceTestCase):

    def test_mail_se_envia_al_paciente(self):
        """el mail de aviso le llega al mail del paciente"""
        enviar_confirmacion_turno(self.turno)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("paciente@test.com", mail.outbox[0].to)

    def test_asunto_contiene_apellido_medico(self):
        """El asunto menciona al médico para que el paciente lo reconozca."""
        enviar_confirmacion_turno(self.turno)

        self.assertIn("García", mail.outbox[0].subject)

    def test_cuerpo_contiene_nombre_paciente(self):
        """El mail saluda al paciente por su nombre."""
        enviar_confirmacion_turno(self.turno)

        self.assertIn("Juan", mail.outbox[0].body)

    def test_retorna_true_cuando_funciona(self):
        """La función retorna True cuando el mail se envía correctamente."""
        resultado = enviar_confirmacion_turno(self.turno)
        self.assertTrue(resultado)
