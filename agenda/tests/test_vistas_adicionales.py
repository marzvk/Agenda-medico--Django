# agenda/tests/test_vistas_adicionales.py
# Flujos de vista que quedaban sin cubrir: validación de semanas, escudos
# de historia clínica, alta/borrado, reserva POST, slot manual y disponibilidad.

from datetime import date, time, timedelta

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from agenda.models import Medico, Paciente, Slot, Turno
from agenda.services.turno_service import TurnoService


class BaseViews(TestCase):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.grupo_secretaria = Group.objects.create(name="Secretaria")

        self.secretaria = User.objects.create_user(
            username="secretaria", password="pass123"
        )
        self.secretaria.is_active = True
        self.secretaria.save()
        self.secretaria.groups.add(self.grupo_secretaria)

        self.user_medico_a = User.objects.create_user(
            username="medico_a", password="pass123"
        )
        self.user_medico_a.is_active = True
        self.user_medico_a.save()
        self.medico_a = Medico.objects.create(
            user=self.user_medico_a,
            nombre="Carlos",
            apellido="García A",
            dni="11111111",
            fecha_nacimiento=date(1980, 1, 1),
            telefono="3735000000",
            email="medico_a@test.com",
            especialidad="Clínica",
            matricula="MAT-A",
            inicio_jornada=time(8, 0),
            fin_jornada=time(18, 0),
            tiempo_consulta=30,
            hora_resumen_diario=time(8, 0),
            horas_recordatorio_paciente=24,
            notificaciones_activas=False,
        )

        self.user_medico_b = User.objects.create_user(
            username="medico_b", password="pass123"
        )
        self.user_medico_b.is_active = True
        self.user_medico_b.save()
        self.medico_b = Medico.objects.create(
            user=self.user_medico_b,
            nombre="Ana",
            apellido="López B",
            dni="22222222",
            fecha_nacimiento=date(1985, 1, 1),
            telefono="3735000001",
            email="medico_b@test.com",
            especialidad="Clínica",
            matricula="MAT-B",
            inicio_jornada=time(8, 0),
            fin_jornada=time(18, 0),
            tiempo_consulta=30,
            hora_resumen_diario=time(8, 0),
            horas_recordatorio_paciente=24,
            notificaciones_activas=False,
        )

        self.paciente_a = Paciente.objects.create(
            nombre="Juan",
            apellido="Corvalán",
            dni="100",
            fecha_nacimiento=date(1990, 5, 10),
            telefono="111",
            email="paciente_a@test.com",
            posee_obra_social=False,
        )
        self.paciente_b = Paciente.objects.create(
            nombre="Ana",
            apellido="Casares",
            dni="200",
            fecha_nacimiento=date(1992, 7, 10),
            telefono="222",
            email="paciente_b@test.com",
            posee_obra_social=True,
            obra_social="OSDE",
        )

        self.slot_a = Slot.objects.create(
            medico=self.medico_a,
            fecha=date.today() - timedelta(days=1),
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            disponible=False,
        )
        self.turno_a = Turno.objects.create(
            slot=self.slot_a,
            paciente=self.paciente_a,
            estado=Turno.EstadoTurno.PROGRAMADO,
        )

        self.slot_b = Slot.objects.create(
            medico=self.medico_b,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            disponible=False,
        )
        self.turno_b = Turno.objects.create(
            slot=self.slot_b,
            paciente=self.paciente_b,
            estado=Turno.EstadoTurno.PROGRAMADO,
        )

    def login_secretaria(self):
        self.client.force_login(self.secretaria)

    def login_medico_a(self):
        self.client.force_login(self.user_medico_a)

    def login_medico_b(self):
        self.client.force_login(self.user_medico_b)


class AgendaMedicoSemanasTest(BaseViews):

    def test_semanas_invalidas_no_rompen(self):
        """?semanas=abc antes explotaba con 500; debe degradar a 1 semana."""
        self.login_secretaria()
        response = self.client.get(
            reverse("agenda:agenda_medico", args=[self.medico_a.id]) + "?semanas=abc"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["semanas_actuales"], "1")


class HistoriaClinicaEscudoTest(BaseViews):

    def test_secretaria_no_puede_editar_historia(self):
        self.login_secretaria()
        response = self.client.get(
            reverse("agenda:editar_historia", args=[self.paciente_a.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_medico_ajeno_no_puede_editar_historia(self):
        """El médico B no puede tocar la historia de un paciente del A."""
        self.login_medico_b()
        response = self.client.get(
            reverse("agenda:editar_historia", args=[self.paciente_a.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_medico_propio_si_puede_editar_historia(self):
        self.login_medico_a()
        response = self.client.get(
            reverse("agenda:editar_historia", args=[self.paciente_a.id])
        )
        self.assertEqual(response.status_code, 200)


class EditarPacienteEscudoTest(BaseViews):

    def test_medico_ajeno_no_puede_editar_paciente(self):
        self.login_medico_b()
        response = self.client.get(
            reverse("agenda:editar_paciente", args=[self.paciente_a.id])
        )
        self.assertEqual(response.status_code, 403)


class SlotManualTest(BaseViews):

    def setUp(self):
        super().setUp()
        # Slot de HOY 10:00-10:30 para probar superposición en la misma fecha.
        self.slot_hoy = Slot.objects.create(
            medico=self.medico_a,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            disponible=True,
        )

    def _post_slot(self, fecha, h_inicio, h_fin):
        return self.client.post(
            reverse("agenda:crear_slot_manual", args=[self.medico_a.id]),
            {"fecha": fecha, "hora_inicio": h_inicio, "hora_fin": h_fin},
        )

    def test_slot_valido_se_crea(self):
        self.login_secretaria()
        antes = Slot.objects.count()
        self._post_slot(date.today().isoformat(), "12:00", "12:30")
        self.assertEqual(Slot.objects.count(), antes + 1)

    def test_superposicion_rechazada(self):
        """Ya existe un slot 10:00-10:30; otro 10:15-10:45 no debe crearse."""
        self.login_secretaria()
        antes = Slot.objects.count()
        self._post_slot(date.today().isoformat(), "10:15", "10:45")
        self.assertEqual(Slot.objects.count(), antes)

    def test_hora_fin_anterior_no_crea_slot(self):
        self.login_secretaria()
        antes = Slot.objects.count()
        self._post_slot(date.today().isoformat(), "12:00", "11:00")
        self.assertEqual(Slot.objects.count(), antes)


class ReservarTurnoTest(BaseViews):

    def test_post_reserva_turno_y_ocupa_slot(self):
        self.login_secretaria()
        slot_libre = Slot.objects.create(
            medico=self.medico_a,
            fecha=date.today(),
            hora_inicio=time(16, 0),
            hora_fin=time(16, 30),
            disponible=True,
        )
        response = self.client.post(
            reverse("agenda:reservar_turno", args=[slot_libre.id]),
            {"paciente_id": self.paciente_a.id},
        )
        self.assertRedirects(
            response, reverse("agenda:agenda_medico", args=[self.medico_a.id])
        )
        slot_libre.refresh_from_db()
        self.assertFalse(slot_libre.disponible)
        self.assertTrue(
            Turno.objects.filter(
                slot=slot_libre, paciente=self.paciente_a, estado="PR"
            ).exists()
        )

    def test_slot_ya_reservado_envia_error(self):
        self.login_secretaria()
        response = self.client.post(
            reverse("agenda:reservar_turno", args=[self.slot_a.id]),
            {"paciente_id": self.paciente_a.id},
        )
        self.assertRedirects(
            response, reverse("agenda:agenda_medico", args=[self.medico_a.id])
        )
        self.assertEqual(Turno.objects.count(), 2)  # solo los del setUp


class CrearPacienteTest(BaseViews):

    def test_post_crea_paciente_y_redirige(self):
        self.login_secretaria()
        response = self.client.post(
            reverse("agenda:crear_paciente"),
            {
                "nombre": "Nueva",
                "apellido": "Paciente",
                "dni": "300",
                "fecha_nacimiento": "1988-03-03",
                "telefono": "333",
                "email": "paciente_n@test.com",
                "historia_clinica": "Sin antecedentes",
                "obra_social": "Particular",
                "posee_obra_social": "",
            },
        )
        self.assertRedirects(response, reverse("agenda:lista_pacientes"))
        self.assertTrue(Paciente.objects.filter(email="paciente_n@test.com").exists())

    def test_medico_no_puede_crear_paciente(self):
        self.login_medico_a()
        response = self.client.get(reverse("agenda:crear_paciente"))
        self.assertEqual(response.status_code, 403)


class BorrarPacienteTest(BaseViews):

    def test_secretaria_puede_borrar(self):
        self.login_secretaria()
        response = self.client.post(
            reverse("agenda:lista_pacientes"),
            {"borrar": "1", "paciente_id": self.paciente_b.id},
        )
        self.assertRedirects(response, reverse("agenda:lista_pacientes"))
        self.assertFalse(Paciente.objects.filter(pk=self.paciente_b.id).exists())

    def test_medico_no_puede_borrar(self):
        self.login_medico_a()
        response = self.client.post(
            reverse("agenda:lista_pacientes"),
            {"borrar": "1", "paciente_id": self.paciente_b.id},
        )
        self.assertRedirects(response, reverse("agenda:lista_pacientes"))
        self.assertTrue(Paciente.objects.filter(pk=self.paciente_b.id).exists())


class GestionarDisponibilidadTest(BaseViews):

    def test_post_actualiza_tiempo_consulta(self):
        self.login_secretaria()
        response = self.client.post(
            reverse("agenda:gestionar_disponibilidad", args=[self.medico_a.id]),
            {
                "tiempo_consulta": "15",
                "disponibilidades-TOTAL_FORMS": "0",
                "disponibilidades-INITIAL_FORMS": "0",
                "disponibilidades-MIN_NUM_FORMS": "0",
                "disponibilidades-MAX_NUM_FORMS": "1000",
            },
        )
        self.assertRedirects(
            response, reverse("agenda:generar_agenda", args=[self.medico_a.id])
        )
        self.medico_a.refresh_from_db()
        self.assertEqual(self.medico_a.tiempo_consulta, 15)


class DetallePacienteTest(BaseViews):

    def test_separa_turnos_futuros_de_historial(self):
        from datetime import timedelta

        slot_futuro = Slot.objects.create(
            medico=self.medico_a,
            fecha=timezone.localdate() + timedelta(days=5),
            hora_inicio=time(11, 0),
            hora_fin=time(11, 30),
            disponible=True,
        )
        TurnoService.crear_turno(slot_futuro, self.paciente_a)

        self.login_secretaria()
        response = self.client.get(
            reverse("agenda:detalle_paciente", args=[self.paciente_a.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["proximos_turnos"]), 1)
        self.assertEqual(len(response.context["historial_turnos"]), 1)