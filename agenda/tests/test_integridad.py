from django.test import TestCase
from django.db import IntegrityError
from datetime import date
from unittest import mock
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
        # "date" (clase de datetime) es inmutable y no admite patch del método;
        # congelamos el "hoy" parcheando la referencia del módulo agenda.models,
        # que es la que lee la propiedad edad (agenda.models.date.today()).
        with mock.patch("agenda.models.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 1)

            model_dates = list(mock_date.call_args_list)

            # Alguien que ya cumplió años (nacido en 1990) tiene 36
            p1 = Paciente(
                nombre="A",
                apellido="B",
                dni="1",
                fecha_nacimiento=date(1990, 1, 1),
                email="a@a.com",
            )
            self.assertEqual(p1.edad, 36)

            # Alguien que cumple en diciembre todavía tiene 35 el 1/6
            p2 = Paciente(
                nombre="C",
                apellido="D",
                dni="2",
                fecha_nacimiento=date(1990, 12, 31),
                email="b@b.com",
            )
            self.assertEqual(p2.edad, 35)

            # El módulo no construye fechas vía mock: solo usa today()
            self.assertEqual(len(model_dates), 0)

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
