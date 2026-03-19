from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta, date, time
import uuid

from agenda.models import Medico, TokenVerificacion

from django.db.models.signals import post_save
from agenda.signals import usuario_post_save


class TokenVerificacionTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="test_user",
            email="test@test.com",
            password="test1234",
            is_active=False,
        )
        self.token = TokenVerificacion.objects.create(
            usuario=self.user,
            tipo=TokenVerificacion.TIPO_ACTIVACION,
        )
        self.user_sin_rol = User.objects.create_user(
            username="sin_rol",
            password="pass123",
            is_active=True,
        )


class TestActivacionCuenta(TokenVerificacionTestCase):

    def test_token_valido_muestra_formulario(self):
        """Token válido muestra el formulario de contraseña."""
        response = self.client.get(reverse("activar_cuenta", args=[self.token.token]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Activar")

    def test_token_inexistente_muestra_invalido(self):
        """Token que no existe muestra la vista de inválido."""
        response = self.client.get(reverse("activar_cuenta", args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "inválido")

    def test_token_expirado_muestra_expirado_y_se_borra(self):
        """
        Token expirado muestra la vista de expirado
        y se elimina de la base de datos.
        """
        # Forzamos la fecha de creación al pasado
        TokenVerificacion.objects.filter(pk=self.token.pk).update(
            creado_en=timezone.now() - timedelta(hours=73)
        )
        self.token.refresh_from_db()

        response = self.client.get(reverse("activar_cuenta", args=[self.token.token]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "expirado")
        self.assertFalse(TokenVerificacion.objects.filter(pk=self.token.pk).exists())

    def test_activacion_correcta_activa_usuario(self):
        """
        Formulario válido activa el usuario y borra el token.
        """
        response = self.client.post(
            reverse("activar_cuenta", args=[self.token.token]),
            {
                "password1": "nueva1234",
                "password2": "nueva1234",
            },
        )

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertFalse(TokenVerificacion.objects.filter(pk=self.token.pk).exists())
        self.assertEqual(response.status_code, 302)

    def test_contrasenas_distintas_no_activan(self):
        """
        Si las contraseñas no coinciden el usuario
        no se activa y el token sigue existiendo.
        """
        self.client.post(
            reverse("activar_cuenta", args=[self.token.token]),
            {
                "password1": "nueva1234",
                "password2": "distinta5678",
            },
        )

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(TokenVerificacion.objects.filter(pk=self.token.pk).exists())


class TestMiddlewareRol(TestCase):

    def setUp(self):
        # Desconectamos la signal para que no interfiera con los tests
        post_save.disconnect(usuario_post_save, sender=User)

        self.client = Client()
        self.grupo_secretaria = Group.objects.create(name="Secretaria")

        # Usuario sin rol
        self.user_sin_rol = User.objects.create_user(
            username="sin_rol",
            password="pass123",
            is_active=True,
        )

        # Usuario secretaria
        self.user_secretaria = User.objects.create_user(
            username="secretaria",
            password="pass123",
            is_active=True,
        )
        self.user_secretaria.groups.add(self.grupo_secretaria)

        # Usuario médico
        self.user_medico = User.objects.create_user(
            username="medico",
            password="pass123",
        )
        self.medico = Medico.objects.create(
            user=self.user_medico,
            nombre="Carlos",
            apellido="García",
            dni="11111111",
            fecha_nacimiento=date(1980, 1, 1),
            telefono="3735000000",
            email="medico@test.com",
            especialidad="Clínica",
            matricula="MAT001",
            inicio_jornada=time(8, 0),
            fin_jornada=time(18, 0),
            tiempo_consulta=30,
            hora_resumen_diario=time(8, 0),
            horas_recordatorio_paciente=24,
            notificaciones_activas=True,
        )

        # Superusuario
        self.admin = User.objects.create_superuser(
            username="admin",
            password="pass123",
            email="admin@test.com",
            is_active=True,
        )

    def tearDown(self):
        # Reconectamos la signal después de cada test
        post_save.connect(usuario_post_save, sender=User)

    def test_usuario_sin_rol_redirige_a_cuenta_pendiente(self):
        """Usuario logueado sin rol no puede acceder a la app."""
        self.client.login(username="sin_rol", password="pass123")
        response = self.client.get(reverse("agenda:index"))
        self.assertRedirects(response, reverse("cuenta_pendiente"))

    def test_secretaria_puede_acceder(self):
        """Secretaria con rol asignado accede normalmente."""
        self.client.login(username="secretaria", password="pass123")
        response = self.client.get(reverse("agenda:index"))
        self.assertEqual(response.status_code, 200)

    def test_medico_puede_acceder(self):
        """Médico con perfil vinculado accede normalmente."""
        self.client.login(username="medico", password="pass123")
        response = self.client.get(reverse("agenda:index"))
        self.assertEqual(response.status_code, 200)

    def test_admin_puede_acceder(self):
        """Superusuario accede normalmente."""
        self.client.login(username="admin", password="pass123")
        response = self.client.get(reverse("agenda:index"))
        self.assertEqual(response.status_code, 200)

    def test_url_admin_no_bloqueada(self):
        """El middleware no bloquea las URLs del admin."""
        self.client.login(username="sin_rol", password="pass123")
        response = self.client.get("/admin/")
        self.assertNotIn("pendiente", response.url)

    def test_url_activacion_no_bloqueada(self):
        """El middleware no bloquea las URLs de activación."""
        self.client.login(username="sin_rol", password="pass123")
        response = self.client.get(f"/accounts/activar/{uuid.uuid4()}/")
        # Devuelve 200 con token inválido, no redirige a cuenta_pendiente
        self.assertEqual(response.status_code, 200)
