import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


# ─── Función genérica ─────────────────────────────────────────────────────────


def enviar_email_html(subject, template_name, context, recipient_list):

    try:
        html_content = render_to_string(template_name, context)
        # strip_tags elimina todas las etiquetas HTML
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        logger.info(f"Mail enviado a {recipient_list} - {subject}")
        return True

    except Exception as e:
        logger.error(f"Error enviando mail a {recipient_list}: {e}")
        return False


# ─── Funciones específicas ────────────────────────────────────────────────────


def enviar_confirmacion_turno(turno):

    medico = turno.slot.medico
    clinica_tel = "3735-XXXXXX"

    context = {
        "paciente": turno.paciente,
        "turno": turno,
        "medico": medico,
        "clinica_telefono": clinica_tel,
    }

    return enviar_email_html(
        subject=f"Turno confirmado - Dr/a. {medico.apellido}",
        template_name="agenda/notificaciones/confirmacion_turno.html",
        context=context,
        recipient_list=[turno.paciente.email],
    )


def enviar_recordatorio_turno(turno_id):
    """
    Recibe ID y no objeto porque Celery serializa argumentos
    como JSON, y los objetos Django no son serializables.
    Siempre pasá IDs a las tareas de Celery.
    """
    from agenda.models import Turno

    try:
        turno = Turno.objects.select_related("paciente", "slot", "slot__medico").get(
            id=turno_id
        )
    except Turno.DoesNotExist:
        logger.warning(f"Recordatorio: turno {turno_id} no existe")
        return False

    if turno.estado == Turno.EstadoTurno.CANCELADO:
        logger.info(f"Recordatorio cancelado: turno {turno_id} fue cancelado")
        return False

    medico = turno.slot.medico
    clinica_tel = "3735-XXXXXX"

    context = {
        "paciente": turno.paciente,
        "turno": turno,
        "medico": medico,
        "clinica_telefono": clinica_tel,
    }

    return enviar_email_html(
        subject=f"Recordatorio de turno - Dr/a. {medico.apellido}",
        template_name="agenda/notificaciones/recordatorio_turno.html",
        context=context,
        recipient_list=[turno.paciente.email],
    )


def enviar_resumen_diario(medico_id):

    from agenda.models import Medico, Turno

    try:
        medico = Medico.objects.get(id=medico_id)
    except Medico.DoesNotExist:
        logger.warning(f"Resumen diario: médico {medico_id} no existe")
        return False

    if not medico.notificaciones_activas:
        return False

    hoy = timezone.localdate()

    turnos = (
        Turno.objects.filter(
            slot__medico=medico,
            slot__fecha=hoy,
            estado=Turno.EstadoTurno.PROGRAMADO,
        )
        .select_related("paciente", "slot")
        .order_by("slot__hora_inicio")
    )

    tiempo_total_minutos = sum(
        (turno.slot.hora_fin.hour * 60 + turno.slot.hora_fin.minute)
        - (turno.slot.hora_inicio.hour * 60 + turno.slot.hora_inicio.minute)
        for turno in turnos
    )

    context = {
        "medico": medico,
        "turnos": turnos,
        "fecha": hoy,
        "total_turnos": turnos.count(),
        "primer_turno": turnos.first(),
        "tiempo_horas": tiempo_total_minutos // 60,
        "tiempo_minutos": tiempo_total_minutos % 60,
        "sin_turnos": not turnos.exists(),
    }

    return enviar_email_html(
        subject=f"Agenda del día {hoy.strftime('%d/%m/%Y')} - {turnos.count()} turnos",
        template_name="agenda/notificaciones/resumen_diario_medico.html",
        context=context,
        recipient_list=[medico.email],
    )


# MANDAR MAIL ACTIVACION
def enviar_activacion_cuenta(usuario, token):
    """Mail al usuario recién creado con el link de activación.
    El link contiene el token UUID que la vista va a verificar."""
    from django.conf import settings

    base_url = getattr(settings, "BASE_URL", "http://127.0.0.1:8000")
    link = f"{base_url}/accounts/activar/{token.token}/"

    context = {
        "usuario": usuario,
        "link": link,
        "horas_expiracion": 72,
    }

    return enviar_email_html(
        subject="Activa tu cuenta en MedAgenda",
        template_name="agenda/notificaciones/activacion_cuenta.html",
        context=context,
        recipient_list=[usuario.email],
    )


def enviar_aviso_usuario_sin_rol(usuario):
    """
    Mail al superusuario avisando que un usuario activó
    su cuenta pero no tiene rol asignado todavía.
    Se manda una sola vez cuando el usuario activa la cuenta.
    """
    from django.contrib.auth.models import User
    from django.conf import settings

    # Buscamos todos los superusuarios para notificarlos
    admins = User.objects.filter(is_superuser=True, email__isnull=False).exclude(
        email=""
    )

    if not admins.exists():
        logger.warning("No hay superusuarios con email para notificar")
        return False

    base_url = getattr(settings, "BASE_URL", "http://127.0.0.1:8000")
    url_admin = f"{base_url}/admin/auth/user/{usuario.id}/change/"

    context = {
        "usuario": usuario,
        "url_admin": url_admin,
    }

    destinatarios = list(admins.values_list("email", flat=True))

    return enviar_email_html(
        subject=f"Usuario {usuario.username} activó su cuenta y espera configuración",
        template_name="agenda/notificaciones/aviso_usuario_sin_rol.html",
        context=context,
        recipient_list=destinatarios,
    )
