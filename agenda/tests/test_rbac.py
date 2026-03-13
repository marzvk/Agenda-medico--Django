# agenda/tests/test_rbac.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from datetime import date, time

from agenda.models import Medico, Paciente, Slot, Turno


class RBACTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # Grupo Secretaria
        self.grupo_secretaria = Group.objects.create(name="Secretaria")

        # Usuario y médico A
        self.user_medico_a = User.objects.create_user(
            username="medico_a", password="pass123"
        )
        self.medico_a = Medico.objects.create(
            user=self.user_medico_a,
            nombre="Carlos",
            apellido="García",
            dni="11111111",
            fecha_nacimiento=date(1980, 1, 1),
            telefono="3735000000",
            email="medico_a@test.com",
            especialidad="Clínica",
            matricula="MAT001",
            inicio_jornada=time(8, 0),
            fin_jornada=time(18, 0),
            tiempo_consulta=30,
            hora_resumen_diario=time(8, 0),
            horas_recordatorio_paciente=24,
            notificaciones_activas=True,
        )

        # Usuario y médico B
        self.user_medico_b = User.objects.create_user(
            username="medico_b", password="pass123"
        )
        self.medico_b = Medico.objects.create(
            user=self.user_medico_b,
            nombre="Ana",
            apellido="López",
            dni="22222222",
            fecha_nacimiento=date(1985, 1, 1),
            telefono="3735000001",
            email="medico_b@test.com",
            especialidad="Pediatría",
            matricula="MAT002",
            inicio_jornada=time(8, 0),
            fin_jornada=time(18, 0),
            tiempo_consulta=30,
            hora_resumen_diario=time(8, 0),
            horas_recordatorio_paciente=24,
            notificaciones_activas=True,
        )

        # Usuario secretaria
        self.user_secretaria = User.objects.create_user(
            username="secretaria", password="pass123"
        )
        self.user_secretaria.groups.add(self.grupo_secretaria)

        # Paciente
        self.paciente = Paciente.objects.create(
            nombre="Juan",
            apellido="Pérez",
            dni="33333333",
            fecha_nacimiento=date(1990, 1, 1),
            telefono="3735000002",
            email="paciente@test.com",
            posee_obra_social=False,
            obra_social="",
        )

        # Slot y turno del médico A
        self.slot = Slot.objects.create(
            medico=self.medico_a,
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


class TestMedicoNoPublicaciones(RBACTestCase):
    """El médico no puede realizar acciones administrativas."""

    def test_medico_no_puede_marcar_asistido(self):
        self.client.login(username="medico_a", password="pass123")
        response = self.client.post(
            reverse("agenda:marcar_asistido", args=[self.turno.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_medico_no_puede_cancelar_turno(self):
        self.client.login(username="medico_a", password="pass123")
        response = self.client.post(
            reverse("agenda:cancelar_turno", args=[self.turno.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_medico_no_puede_reservar_turno(self):
        slot_libre = Slot.objects.create(
            medico=self.medico_a,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            disponible=True,
        )
        self.client.login(username="medico_a", password="pass123")
        response = self.client.get(
            reverse("agenda:reservar_turno", args=[slot_libre.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_medico_no_puede_crear_paciente(self):
        self.client.login(username="medico_a", password="pass123")
        response = self.client.get(reverse("agenda:crear_paciente"))
        self.assertEqual(response.status_code, 403)

    def test_medico_no_puede_gestionar_disponibilidad_ajena(self):
        self.client.login(username="medico_a", password="pass123")
        response = self.client.get(
            reverse("agenda:gestionar_disponibilidad", args=[self.medico_b.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_medico_no_puede_ver_agenda_ajena(self):
        self.client.login(username="medico_a", password="pass123")
        response = self.client.get(
            reverse("agenda:agenda_medico", args=[self.medico_b.id])
        )
        self.assertEqual(response.status_code, 403)


class TestSecretariaPuedeOperar(RBACTestCase):
    """La secretaria puede realizar todas las acciones administrativas."""

    def test_secretaria_puede_marcar_asistido(self):
        self.client.login(username="secretaria", password="pass123")
        response = self.client.post(
            reverse("agenda:marcar_asistido", args=[self.turno.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_secretaria_puede_cancelar_turno(self):
        self.client.login(username="secretaria", password="pass123")
        response = self.client.post(
            reverse("agenda:cancelar_turno", args=[self.turno.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_secretaria_puede_crear_paciente(self):
        self.client.login(username="secretaria", password="pass123")
        response = self.client.get(reverse("agenda:crear_paciente"))
        self.assertEqual(response.status_code, 200)


class TestUsuarioNoLogueado(RBACTestCase):
    """Usuario sin login redirige al login en todas las vistas protegidas."""

    def test_no_logueado_redirige_en_marcar_asistido(self):
        response = self.client.post(
            reverse("agenda:marcar_asistido", args=[self.turno.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_no_logueado_redirige_en_cancelar_turno(self):
        response = self.client.post(
            reverse("agenda:cancelar_turno", args=[self.turno.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)


class TestSlotManual(RBACTestCase):

    def test_medico_puede_crear_slot_en_su_propia_agenda(self):
        self.client.login(username="medico_a", password="pass123")
        response = self.client.post(
            reverse("agenda:crear_slot_manual", args=[self.medico_a.id]),
            {
                "fecha": date.today(),
                "hora_inicio": "15:00",
                "hora_fin": "15:30",
            },
        )
        # Redirige porque el slot se creó correctamente
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Slot.objects.filter(medico=self.medico_a, hora_inicio="15:00").exists()
        )

    def test_medico_no_puede_crear_slot_en_agenda_ajena(self):
        self.client.login(username="medico_a", password="pass123")
        response = self.client.post(
            reverse("agenda:crear_slot_manual", args=[self.medico_b.id]),
            {
                "fecha": date.today(),
                "hora_inicio": "15:00",
                "hora_fin": "15:30",
            },
        )
        self.assertEqual(response.status_code, 403)
