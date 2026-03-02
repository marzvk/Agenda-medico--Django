from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date, time
from django.core.exceptions import ValidationError

from ..models import Turno, DisponibilidadSemanal
from ..services.turno_service import TurnoService
from ..models import Medico, Paciente, Slot


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
