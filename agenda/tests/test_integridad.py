from django.test import TestCase
from django.db import IntegrityError
from datetime import date
from agenda.models import Medico, Paciente, Slot


class ModelosIntegridadTest(TestCase):
    def setUp(self):
        # Datos base para los tests
        self.medico = Medico.objects.create(
            nombre="Gregory",
            apellido="House",
            dni="123",
            fecha_nacimiento=date(1970, 5, 15),
            email="house@med.com",
            especialidad="Diagnóstico",
            inicio_jornada="08:00",
            fin_jornada="16:00",
            telefono="111",
        )

    def test_calculo_edad_exacto(self):
        # Caso 1: Alguien que ya cumplió años este año (nacido en 1990)
        p1 = Paciente(
            nombre="A",
            apellido="B",
            dni="1",
            fecha_nacimiento=date(1990, 1, 1),
            email="a@a.com",
        )
        # En 2026, ya tiene 36
        self.assertEqual(p1.edad, 36)

        # Caso 2: Alguien que cumple en diciembre (aún no cumplió en marzo)
        p2 = Paciente(
            nombre="C",
            apellido="D",
            dni="2",
            fecha_nacimiento=date(1990, 12, 31),
            email="b@b.com",
        )
        # En marzo 2026, todavía tiene 35
        self.assertEqual(p2.edad, 35)

    def test_unicidad_slot_medico(self):
        fecha_test = date.today()
        hora_test = "10:00"

        Slot.objects.create(
            medico=self.medico,
            fecha=fecha_test,
            hora_inicio=hora_test,
            hora_fin="10:30",
        )

        with self.assertRaises(IntegrityError):
            Slot.objects.create(
                medico=self.medico,
                fecha=fecha_test,
                hora_inicio=hora_test,
                hora_fin="10:30",
            )
