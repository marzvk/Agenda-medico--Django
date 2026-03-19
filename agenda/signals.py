import json
import logging
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.contrib.auth.models import User
from agenda.models import TokenVerificacion


logger = logging.getLogger(__name__)


def _nombre_tarea_medico(medico):
    """
    PeriodicTask requiere nombres únicos en la base de datos.
    Usamos el id del médico para garantizarlo.
    """
    return f"resumen_diario_medico_{medico.id}"


#
def _actualizar_beat_para_medico(medico):
    """Crea o actualiza el schedule de Beat para un medico"""

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=medico.hora_resumen_diario.minute,
        hour=medico.hora_resumen_diario.hour,
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone="America/Argentina/Buenos_Aires",
    )

    PeriodicTask.objects.update_or_create(
        name=_nombre_tarea_medico(medico),
        defaults={
            "task": "agenda.notifications.tasks.tarea_resumen_diario",
            "crontab": schedule,
            "args": json.dumps([medico.id]),
            "enabled": medico.notificaciones_activas,
        },
    )
    logger.info(
        f"Beat actualizado para medico {medico,id} a las {medico.hora_resumen_diario}"
    )


#
@receiver(post_save, sender="agenda.Medico")
def medico_post_save(sender, instance, **kwargs):
    """Se dispara automáticamente cada vez que se guarda un Medico.
    instance es el objeto Medico que se acaba de guardar."""
    _actualizar_beat_para_medico(instance)


#
@receiver(post_delete, sender="agenda.Medico")
def medico_post_delete(sender, instance, **kwargs):
    """Se dispara cuando se borra un medico, borra las tareas que le pertenecian que nunca se van a correr"""
    try:
        PeriodicTask.objects.filter(name=_nombre_tarea_medico(instance)).delete()
        logger.info(f"Tarea Beat eliminada para médico {instance.id}")
    except Exception as e:
        logger.error(f"Error eliminando tarea Beat para médico {instance.id}: {e}")


#
@receiver(post_save, sender=User)
def usuario_post_save(sender, instance, created, **kwargs):
    """
    Se dispara cuando se crea un usuario nuevo.
    Solo actúa en la creación (created=True), no en modificaciones.
    Genera el token y manda el mail de activación.
    """
    if not created:
        return

    # superuser no necesita mail de activacion
    if instance.is_superuser:
        return

    User.objects.filter(pk=instance.pk).update(is_active=False)

    # generacion token
    token = TokenVerificacion.objects.create(
        usuario=instance,
        tipo=TokenVerificacion.TIPO_ACTIVACION,
    )

    from agenda.notifications.email_service import enviar_activacion_cuenta

    enviar_activacion_cuenta(instance, token)
    logger.info(f"Mail de activacion enviado a {instance.email}")
