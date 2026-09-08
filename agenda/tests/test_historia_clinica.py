from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date, time

from agenda.models import Medico, Paciente, Slot, Turno


class HistoriaClinicaAppendTest(TestCase):

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="dr_historia", password="pass123"
        )
        self.user.is_active = True
        self.user.save()

        self.medico = Medico.objects.create(
            user=self.user,
            nombre="Ana",
            apellido="Médica",
            dni="77777777",
            fecha_nacimiento=date(1980, 1, 1),
            telefono="3735000000",
            email="dr_historia@test.com",
            especialidad="Clínica",
            matricula="MAT99",
            inicio_jornada=time(8, 0),
            fin_jornada=time(18, 0),
            tiempo_consulta=30,
            hora_resumen_diario=time(8, 0),
            notificaciones_activas=False,
        )

        self.paciente = Paciente.objects.create(
            nombre="Juan",
            apellido="Paciente",
            dni="88888888",
            fecha_nacimiento=date(1990, 5, 10),
            telefono="3735000001",
            email="paciente_historia@test.com",
            historia_clinica="Antecedente previo",
            posee_obra_social=False,
            obra_social="",
        )

        slot = Slot.objects.create(
            medico=self.medico,
            fecha=date.today(),
            hora_inicio=time(9, 0),
            hora_fin=time(9, 30),
        )
        Turno.objects.create(slot=slot, paciente=self.paciente, estado="PR")

    def test_agregar_evolucion_preserva_historial(self):
        self.paciente.agregar_evolucion("Nueva evolución A")
        self.paciente.refresh_from_db()

        self.assertIn("Nueva evolución A", self.paciente.historia_clinica)
        self.assertIn("Antecedente previo", self.paciente.historia_clinica)
        self.assertLess(
            self.paciente.historia_clinica.index("Nueva evolución A"),
            self.paciente.historia_clinica.index("Antecedente previo"),
        )

    def test_agregar_evolucion_vacia_rechazada(self):
        with self.assertRaises(ValidationError):
            self.paciente.agregar_evolucion("   ")

    def test_vista_editar_historia_hace_append(self):
        self.client.login(username="dr_historia", password="pass123")
        response = self.client.post(
            reverse("agenda:editar_historia", args=[self.paciente.id]),
            {"historia_clinica": "Nueva evolución desde vista"},
        )

        self.assertEqual(response.status_code, 302)
        self.paciente.refresh_from_db()
        self.assertIn("Nueva evolución desde vista", self.paciente.historia_clinica)
        self.assertIn("Antecedente previo", self.paciente.historia_clinica)

    def test_vista_editar_historia_acumula_sin_duplicar(self):
        self.client.login(username="dr_historia", password="pass123")
        for nota in ("Primera nota", "Segunda nota"):
            self.client.post(
                reverse("agenda:editar_historia", args=[self.paciente.id]),
                {"historia_clinica": nota},
            )

        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.historia_clinica.count("Primera nota"), 1)
        self.assertEqual(self.paciente.historia_clinica.count("Segunda nota"), 1)
        self.assertLess(
            self.paciente.historia_clinica.index("Segunda nota"),
            self.paciente.historia_clinica.index("Primera nota"),
        )