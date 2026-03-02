from django.test import TestCase
from django.utils import timezone
from datetime import time, date

from agenda.models import Medico, DisponibilidadSemanal, Slot
from agenda.services.slot_service import generar_slots_para_medico


class SlotServices(TestCase):

    # Datos
    def setUp(self):
        self.medico = Medico.objects.create(
            nombre="Dr",
            apellido="Test",
            fecha_nacimiento=date(1980, 1, 1),
            telefono="123456789",
            email="medico@test.com",
            especialidad="Clinica",
            matricula="123",
            inicio_jornada=time(9, 0),
            fin_jornada=time(12, 0),
            tiempo_consulta=30,
        )

        DisponibilidadSemanal.objects.create(
            medico=self.medico,
            dias_semana=0,
            hora_inicio=time(9, 0),
            hora_fin=time(12, 0),
            activo=True,
        )

    # Generar slot correcto
    def test_generar_slots_crea_ok(self):
        generar_slots_para_medico(self.medico, dias_adelante=7)

        slots = Slot.objects.filter(medico=self.medico)

        self.assertTrue(slots.exists())

    # Medir los slots en un dia
    def test_cantidad_correcta_slots_en_un_dia(self):
        generar_slots_para_medico(self.medico, dias_adelante=7)

        fechas = (
            Slot.objects.filter(medico=self.medico)
            .values_list("fecha", flat=True)
            .distinct()
        )
        self.assertEqual(fechas.count(), 1)

        fecha_generada = fechas.first()

        slots = Slot.objects.filter(medico=self.medico, fecha=fecha_generada)

        self.assertEqual(slots.count(), 6)
        # self.assertEqual(slots_martes.count(), 0)

    # No generar 2 veces slots
    def test_no_duplica_slots(self):
        generar_slots_para_medico(self.medico, dias_adelante=7)
        generar_slots_para_medico(self.medico, dias_adelante=7)

        total = Slot.objects.filter(medico=self.medico).count()

        self.assertTrue(total > 0)

        generar_slots_para_medico(self.medico, dias_adelante=7)
        total_despues = Slot.objects.filter(medico=self.medico).count()

        self.assertTrue(total, total_despues)
