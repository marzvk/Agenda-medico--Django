from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta, date, time
from django.core.exceptions import ValidationError
from unittest import mock

from ..models import Turno, DisponibilidadSemanal
from ..services.turno_service import TurnoService
from ..models import Medico, Paciente, Slot
from agenda.notifications import tasks as tareas


class TurnoServiceTest(TestCase):

    def setUp(self):
        self.medico = Medico.objects.create(
            nombre="Juan",
            apellido="Perez",
            fecha_nacimiento=date(1980, 1, 1),
            telefono="123456789",
            email="medico@test.com",
            especialidad="Clinica",
            matricula="ABC123",
            inicio_jornada=time(8, 0),
            fin_jornada=time(16, 0),
        )

        self.paciente = Paciente.objects.create(
            nombre="Maria",
            apellido="Gomez",
            fecha_nacimiento=date(1995, 5, 5),
            telefono="987654321",
            email="paciente@test.com",
            historia_clinica="Sin antecedentes",
            posee_obra_social=True,
            obra_social="OSDE",
        )

        # self.medico = Medico.objects.create(nombre="Dr test")
        # self.paciente = Paciente.objects.create(nombre="Paciente test")

        self.slot = Slot.objects.create(
            medico=self.medico,
            fecha=date(2026, 3, 9),
            hora_inicio=time(9, 0),
            hora_fin=time(9, 30),
            disponible=True,
        )

    # USA UN SLOT
    def test_crear_turno_ocupa_slot(self):
        TurnoService.crear_turno(self.slot, self.paciente)

        self.slot.refresh_from_db()

        self.assertEqual(Turno.objects.count(), 1)
        self.assertFalse(self.slot.disponible)

    # NO PODER RESERVAR UN SLOT OCUPADO
    def test_no_permite_reservar_slot_ocupado(self):

        TurnoService.crear_turno(self.slot, self.paciente)

        with self.assertRaises(ValidationError):
            TurnoService.crear_turno(self.slot, self.paciente)

        self.assertEqual(Turno.objects.count(), 1)

    # DEJAR LIBRE EL SLOT
    def test_cancelar_turno_libera_slot(self):

        turno = TurnoService.crear_turno(self.slot, self.paciente)

        TurnoService.cancelar_turno(turno)

        self.slot.refresh_from_db()
        turno.refresh_from_db()

        self.assertEqual(turno.estado, Turno.EstadoTurno.CANCELADO)
        self.assertTrue(self.slot.disponible)

    def test_programar_notificacion_se_difiere_al_commit(self):
        """La notificación se registra como callback on_commit, no se ejecuta
        dentro de la transacción.

        Si el envío a Celery corriera dentro de la transacción, un fallo de
        broker/worker rompería la creación del turno, y el worker podría
        leer el turno antes de que exista (raza de concurrencia).
        """
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            TurnoService.crear_turno(self.slot, self.paciente)

        # El callback queda pendiente de ejecutar tras el commit
        self.assertEqual(len(callbacks), 1)

        self.slot.refresh_from_db()
        self.assertFalse(self.slot.disponible)

    def test_notificaciones_activas_se_ejecutan_tras_commit(self):
        """Con notificaciones activas, el envío ocurre POST commit."""
        slot_futuro = Slot.objects.create(
            medico=self.medico,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            disponible=True,
        )

        with mock.patch.object(tareas.tarea_confirmacion_turno, "delay") as mock_delay, \
             mock.patch.object(tareas.tarea_recordatorio_turno, "apply_async") as mock_async:
            with self.captureOnCommitCallbacks(execute=True):
                TurnoService.crear_turno(slot_futuro, self.paciente)

        mock_delay.assert_called_once()
        mock_async.assert_called_once()

    def test_medico_inactivo_no_ejecuta_notificaciones(self):
        """Con notificaciones desactivadas el callback no encola nada."""
        self.medico.notificaciones_activas = False
        self.medico.save()

        slot_futuro = Slot.objects.create(
            medico=self.medico,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(11, 0),
            hora_fin=time(11, 30),
            disponible=True,
        )

        with mock.patch.object(tareas.tarea_confirmacion_turno, "delay") as mock_delay, \
             mock.patch.object(tareas.tarea_recordatorio_turno, "apply_async") as mock_async:
            with self.captureOnCommitCallbacks(execute=True):
                TurnoService.crear_turno(slot_futuro, self.paciente)

        mock_delay.assert_not_called()
        mock_async.assert_not_called()

        slot_futuro.refresh_from_db()
        self.assertFalse(slot_futuro.disponible)

    def test_confirmacion_se_encola_con_id_del_turno(self):
        """delay recibe el ID del turno (Celery serializa JSON, no objetos)."""
        slot_futuro = Slot.objects.create(
            medico=self.medico,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            disponible=True,
        )

        with mock.patch.object(tareas.tarea_confirmacion_turno, "delay") as mock_delay, \
             mock.patch.object(tareas.tarea_recordatorio_turno, "apply_async"):
            with self.captureOnCommitCallbacks(execute=True):
                turno = TurnoService.crear_turno(slot_futuro, self.paciente)

        mock_delay.assert_called_once_with(turno.id)

    def test_eta_recordatorio_calculado_correctamente(self):
        """
        apply_async recibe eta = fecha_hora del turno − horas_recordatorio_paciente.
        Es el corazón del "avisame X horas antes".
        """
        slot_futuro = Slot.objects.create(
            medico=self.medico,
            fecha=date.today() + timedelta(days=4),
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            disponible=True,
        )
        self.medico.horas_recordatorio_paciente = 24

        with mock.patch.object(tareas.tarea_confirmacion_turno, "delay"), \
             mock.patch.object(tareas.tarea_recordatorio_turno, "apply_async") as mock_async:
            with self.captureOnCommitCallbacks(execute=True):
                TurnoService.crear_turno(slot_futuro, self.paciente)

        mock_async.assert_called_once()
        eta = mock_async.call_args.kwargs["eta"]

        turno_datetime = datetime.combine(
            slot_futuro.fecha,
            slot_futuro.hora_inicio,
            tzinfo=timezone.get_current_timezone(),
        )
        self.assertEqual(eta, turno_datetime - timedelta(hours=24))

    def test_eta_pasado_no_encola_recordatorio(self):
        """
        Si el turno es tan próximo que el usuero ya debería estar avisado
        (eta < ahora), NO se agenda el recordatorio.
        Caso real: crear un turno a 12h con recordatorio configurado a 24h.
        """
        self.medico.horas_recordatorio_paciente = 24

        objetivo = timezone.localtime() + timedelta(hours=12)
        slot_proximo = Slot.objects.create(
            medico=self.medico,
            fecha=objetivo.date(),
            hora_inicio=objetivo.time(),
            hora_fin=(objetivo + timedelta(minutes=30)).time(),
            disponible=True,
        )

        with mock.patch.object(tareas.tarea_confirmacion_turno, "delay") as mock_delay, \
             mock.patch.object(tareas.tarea_recordatorio_turno, "apply_async") as mock_async:
            with self.captureOnCommitCallbacks(execute=True):
                TurnoService.crear_turno(slot_proximo, self.paciente)
            self.slot.refresh_from_db()

        mock_delay.assert_called_once()
        mock_async.assert_not_called()
