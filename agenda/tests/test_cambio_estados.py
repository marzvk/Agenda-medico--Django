from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from agenda.models import Medico, Paciente, Slot, Turno


class AccionesTurnoTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Setup mínimo (Persona campos obligatorios)
        self.medico = Medico.objects.create(
            nombre="Dr",
            apellido="Test",
            dni="111",
            fecha_nacimiento=date(1980, 1, 1),
            email="dr@test.com",
            especialidad="Test",
            inicio_jornada="08:00",
            fin_jornada="16:00",
        )
        self.paciente = Paciente.objects.create(
            nombre="P",
            apellido="T",
            dni="222",
            fecha_nacimiento=date(1990, 1, 1),
            email="p@test.com",
            posee_obra_social=False,
        )
        self.slot = Slot.objects.create(
            medico=self.medico,
            fecha=date.today(),
            hora_inicio="09:00",
            hora_fin="09:30",
        )
        # Turno inicial en estado PROGRAMADO ('PR')
        self.turno = Turno.objects.create(
            paciente=self.paciente, slot=self.slot, estado="PR"
        )

    def test_marcar_asistido_actualiza_db(self):
        """Verifica que la URL marcar_asistido cambie el estado a 'AS'"""
        # Llamamos a la URL de la acción
        response = self.client.post(
            reverse("agenda:marcar_asistido", args=[self.turno.id])
        )

        # Refrescamos el objeto desde la base de datos
        self.turno.refresh_from_db()

        self.assertEqual(self.turno.estado, "AS")
        # Normalmente estas vistas redirigen (302) a la home después de la acción
        self.assertEqual(response.status_code, 302)

    def test_cancelar_turno_actualiza_db(self):
        """Verifica que la URL cancelar_turno cambie el estado a 'CA'"""
        response = self.client.post(
            reverse("agenda:cancelar_turno", args=[self.turno.id])
        )

        self.turno.refresh_from_db()

        self.assertEqual(self.turno.estado, "CA")
        self.assertEqual(response.status_code, 302)
