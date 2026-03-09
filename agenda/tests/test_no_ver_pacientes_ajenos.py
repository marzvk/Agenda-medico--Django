from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from agenda.models import Paciente, Medico, Slot, Turno
from datetime import date, time


class PacientePrivacidadTest(TestCase):
    def setUp(self):
        # 1. Usuarios
        self.user_a = User.objects.create_user(username="dr_a", password="pass123")
        self.user_b = User.objects.create_user(username="dr_b", password="pass123")

        # 2. Médicos (Completando todos los campos de Persona + Medico)
        self.medico_a = Medico.objects.create(
            user=self.user_a,
            nombre="Dr",
            apellido="ApellidoUnicoA",
            dni="1",
            fecha_nacimiento=date(1980, 1, 1),
            telefono="111",
            email="dr_a@test.com",
            matricula="M1",
            inicio_jornada=time(8, 0),
            fin_jornada=time(17, 0),
        )
        self.medico_b = Medico.objects.create(
            user=self.user_b,
            nombre="Dr",
            apellido="BapellidoBunico",
            dni="2",
            fecha_nacimiento=date(1985, 1, 1),
            telefono="222",
            email="dr_b@test.com",
            matricula="M2",
            inicio_jornada=time(8, 0),
            fin_jornada=time(17, 0),
        )

        # 3. Pacientes (Completando Persona + Paciente)
        self.paciente_a = Paciente.objects.create(
            nombre="Juan",
            apellido="De_A",
            dni="100",
            fecha_nacimiento=date(1990, 5, 10),
            telefono="555",
            email="juan@test.com",
            posee_obra_social=False,
            obra_social="Ninguna",
        )
        self.paciente_b = Paciente.objects.create(
            nombre="Pedro",
            apellido="De_B",
            dni="200",
            fecha_nacimiento=date(1995, 8, 20),
            telefono="666",
            email="pedro@test.com",
            posee_obra_social=False,
            obra_social="Ninguna",
        )

        # 4. Slots y Turnos para generar el vínculo
        slot_a = Slot.objects.create(
            medico=self.medico_a,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
        )
        Turno.objects.create(slot=slot_a, paciente=self.paciente_a, estado="PR")

        slot_b = Slot.objects.create(
            medico=self.medico_b,
            fecha=date.today(),
            hora_inicio=time(11, 0),
            hora_fin=time(11, 30),
        )
        Turno.objects.create(slot=slot_b, paciente=self.paciente_b, estado="PR")

    def test_medico_solo_ve_sus_pacientes(self):
        self.client.login(username="dr_a", password="pass123")
        response = self.client.get(reverse("agenda:lista_pacientes"))

        # Verificamos que la respuesta fue exitosa
        self.assertEqual(response.status_code, 200)

        # Usamos el objeto directo para evitar errores de tipeo
        self.assertContains(response, self.paciente_a.apellido.upper())
        self.assertNotContains(response, self.paciente_b.apellido.upper())

    def test_medico_no_puede_ver_detalle_ajeno(self):
        # El Dr A intenta entrar por URL al detalle del paciente del Dr B
        self.client.login(username="dr_a", password="pass123")

        url_ajena = reverse(
            "agenda:detalle_paciente", kwargs={"paciente_id": self.paciente_b.id}
        )
        response = self.client.get(url_ajena)

        # Debería dar un 403 Forbidden por el escudo de PermissionDenied
        self.assertEqual(response.status_code, 403)
