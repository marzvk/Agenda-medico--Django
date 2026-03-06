from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta
from agenda.models import Medico, Paciente, Slot, Turno


class AgendaVistasTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Creamos la data necesaria (Persona tiene campos obligatorios)
        self.medico = Medico.objects.create(
            nombre="Gregory",
            apellido="House",
            dni="123",
            fecha_nacimiento=date(1970, 1, 1),
            email="h@med.com",
            especialidad="Diagnóstico",
            inicio_jornada="08:00",
            fin_jornada="16:00",
        )
        self.paciente = Paciente.objects.create(
            nombre="Will",
            apellido="Wilson",
            dni="456",
            fecha_nacimiento=date(1990, 1, 1),
            email="w@pac.com",
            posee_obra_social=True,
        )

        # Turno para HOY
        self.slot_hoy = Slot.objects.create(
            medico=self.medico,
            fecha=date.today(),
            hora_inicio="10:00",
            hora_fin="10:30",
        )
        self.turno_hoy = Turno.objects.create(
            paciente=self.paciente, slot=self.slot_hoy, estado="PR"
        )

        # Turno para dentro de 10 días (Fuera del rango semanal por defecto)
        self.slot_lejos = Slot.objects.create(
            medico=self.medico,
            fecha=date.today() + timedelta(days=10),
            hora_inicio="11:00",
            hora_fin="11:30",
        )
        self.turno_lejos = Turno.objects.create(
            paciente=self.paciente, slot=self.slot_lejos, estado="PR"
        )

    def test_rango_semanal_por_defecto(self):
        """Verifica que sin filtros solo traiga la agenda de la semana (6 días)"""
        response = self.client.get(reverse("agenda:index"))
        # El de hoy debe estar, el de 10 días NO
        self.assertIn(self.turno_hoy, response.context["turnos"])
        self.assertNotIn(self.turno_lejos, response.context["turnos"])

    def test_filtro_medico_vacio(self):
        """Verifica que si filtro un médico sin turnos, la lista esté vacía"""
        otro_medico = Medico.objects.create(
            nombre="Mandy",
            apellido="Cullen",
            dni="999",
            fecha_nacimiento=date(1980, 1, 1),
            email="m@med.com",
            especialidad="Pediatría",
            inicio_jornada="08:00",
            fin_jornada="16:00",
        )
        response = self.client.get(reverse("agenda:index"), {"medico": otro_medico.id})
        self.assertEqual(len(response.context["turnos"]), 0)

    def test_exclusion_cancelados(self):
        """Asegura que los turnos cancelados 'CA' no se muestren"""
        self.turno_hoy.estado = "CA"
        self.turno_hoy.save()
        response = self.client.get(reverse("agenda:index"))
        self.assertNotIn(self.turno_hoy, response.context["turnos"])
