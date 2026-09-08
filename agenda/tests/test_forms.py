# agenda/tests/test_forms.py
# Validaciones nuevas de Fase A (SlotForm) y Fase B (EstablecerContrasenaForm).

from django.test import TestCase
from datetime import date, time, timedelta
from django.contrib.auth.models import User
from django.utils import timezone

from agenda.forms import SlotForm
from agenda.models import Medico
from agenda.views.auth_views import EstablecerContrasenaForm


class SlotFormTest(TestCase):

    def setUp(self):
        self.medico = Medico.objects.create(
            nombre="Carlos",
            apellido="García",
            dni="12345678",
            fecha_nacimiento=date(1980, 1, 1),
            email="medico@test.com",
            especialidad="Kinesiología",
            matricula="MAT001",
            inicio_jornada=time(8, 0),
            fin_jornada=time(18, 0),
            tiempo_consulta=30,
        )

    def _form(self, **kwargs):
        datos = {
            "fecha": timezone.localdate().isoformat(),
            "hora_inicio": "09:00",
            "hora_fin": "09:30",
        }
        datos.update(kwargs)
        return SlotForm(data=datos, medico=self.medico)

    def test_valid_happy_path(self):
        form = self._form()
        self.assertTrue(form.is_valid(), form.errors)

    def test_hora_fin_anterior_a_inicio_invalida(self):
        form = self._form(hora_inicio="10:00", hora_fin="09:00")
        self.assertFalse(form.is_valid())

    def test_hora_fin_igual_a_inicio_invalida(self):
        form = self._form(hora_inicio="10:00", hora_fin="10:00")
        self.assertFalse(form.is_valid())

    def test_fecha_pasada_invalida(self):
        form = self._form(fecha=(timezone.localdate() - timedelta(days=1)).isoformat())
        self.assertFalse(form.is_valid())

    def test_fecha_demasiado_lejana_invalida(self):
        form = self._form(fecha=(timezone.localdate() + timedelta(days=370)).isoformat())
        self.assertFalse(form.is_valid())

    def test_fuera_de_jornada_invalida(self):
        form = self._form(hora_inicio="07:00", hora_fin="07:30")
        self.assertFalse(form.is_valid())


class EstablecerContrasenaFormTest(TestCase):

    def setUp(self):
        self.user_placeholder = User(
            username="test_user", email="test@test.com"
        )

    def _form(self, **kwargs):
        datos = {"password1": "nueva1234", "password2": "nueva1234"}
        datos.update(kwargs)
        return EstablecerContrasenaForm(data=datos, usuario=self.user_placeholder)

    def test_contrasena_valida_pasa(self):
        form = self._form()
        self.assertTrue(form.is_valid(), form.errors)

    def test_numerica_es_rechazada(self):
        form = self._form(password1="12345678", password2="12345678")
        self.assertFalse(form.is_valid())

    def test_similar_al_username_es_rechazada(self):
        form = self._form(password1="test_user", password2="test_user")
        self.assertFalse(form.is_valid())

    def test_distintas_son_rechazadas(self):
        form = self._form(password2="distinta5678")
        self.assertFalse(form.is_valid())