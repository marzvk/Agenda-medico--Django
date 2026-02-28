from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date, time
from django.core.exceptions import ValidationError

from .models import Turno, DisponibilidadSemanal
from .services.turno_service import TurnoService
from .models import Medico, Paciente


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

    # CREA TURNO PRUEBA
    def test_crea_turno_valido(self):
        fecha = timezone.now() + timedelta(days=1)
        fecha = fecha.replace(hour=9, minute=0, second=0, microsecond=0)
        dia = fecha.weekday()

        datos = {
            "medico": self.medico,
            "paciente": self.paciente,
            "fecha_hora": fecha,
            "duracion_minutos": 30,
        }
        DisponibilidadSemanal.objects.create(
            medico=self.medico,
            dias_semana=dia,
            hora_inicio=time(8, 0),
            hora_fin=time(16, 0),
            activo=True,
        )

        turno = TurnoService.crear_turno(datos)

        self.assertEqual(Turno.objects.count(), 1)
        self.assertEqual(turno.medico, self.medico)
        self.assertEqual(turno.paciente, self.paciente)
        self.assertEqual(turno.estado, Turno.EstadoTurno.PROGRAMADO)

    # NO DEBERIA CREAR
    def test_no_crea_turno_fuera_de_horario(self):
        fecha = timezone.now() + timedelta(days=1)
        fecha = fecha.replace(hour=18, minute=0, second=0, microsecond=0)
        dia = fecha.weekday()

        DisponibilidadSemanal.objects.create(
            medico=self.medico,
            dias_semana=dia,
            hora_inicio=time(8, 0),
            hora_fin=time(16, 0),
            activo=True,
        )

        datos = {
            "medico": self.medico,
            "paciente": self.paciente,
            "fecha_hora": fecha,
            "duracion_minutos": 30,
        }
        with self.assertRaises(ValidationError):
            TurnoService.crear_turno(datos)

        self.assertEqual(Turno.objects.count(), 0)

    # NO DEBE PERMITIR SUPERPONER SI YA EXISTE
    def test_no_crea_turno_superpuesto(self):
        fecha = timezone.now() + timedelta(days=1)
        fecha = fecha.replace(hour=9, minute=0, second=0, microsecond=0)
        dia = fecha.weekday()

        DisponibilidadSemanal.objects.create(
            medico=self.medico,
            dias_semana=dia,
            hora_inicio=time(8, 0),
            hora_fin=time(16, 0),
            activo=True,
        )

        datos1 = {
            "medico": self.medico,
            "paciente": self.paciente,
            "fecha_hora": fecha,
            "duracion_minutos": 30,
        }
        TurnoService.crear_turno(datos1)

        fecha_encimada = fecha + timedelta(minutes=15)

        datos2 = {
            "medico": self.medico,
            "paciente": self.paciente,
            "fecha_hora": fecha_encimada,
            "duracion_minutos": 30,
        }

        with self.assertRaises(ValidationError):
            TurnoService.crear_turno(datos2)

        self.assertEqual(Turno.objects.count(), 1)

    # NO TURNO EN UN DIA NO DISPONIBLE
    def test_no_crea_turno_dia_no_disponible(self):

        fecha = timezone.now() + timedelta(days=1)
        fecha = fecha.replace(hour=9, minute=0, second=0, microsecond=0)
        dia_real = fecha.weekday()

        dia_distinto = (dia_real + 1) % 7

        DisponibilidadSemanal.objects.create(
            medico=self.medico,
            dias_semana=dia_distinto,
            hora_inicio=time(8, 0),
            hora_fin=time(16, 0),
            activo=True,
        )

        datos = {
            "medico": self.medico,
            "paciente": self.paciente,
            "fecha_hora": fecha,
            "duracion_minutos": 30,
        }

        with self.assertRaises(ValidationError):
            TurnoService.crear_turno(datos)

        self.assertEqual(Turno.objects.count(), 0)
