import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def tarea_confirmacion_turno(turno_id):
    """
    Se dispara inmediatamente cuando se crea un turno.
    Recibe el ID y no el objeto por una razón importante:
    Celery serializa los argumentos a JSON para guardarlos en Redis,
    y los objetos Django no son serializables.
    """
    from agenda.notifications.email_service import enviar_confirmacion_turno
    from agenda.models import Turno

    try:
        turno = Turno.objects.select_related("paciente", "slot", "slot__medico").get(
            id=turno_id
        )
        enviar_confirmacion_turno(turno)
        logger.info(f"Confirmación enviada para turno {turno_id}")
    except Turno.DoesNotExist:
        logger.warning(f"tarea_confirmacion_turno: turno {turno_id} no existe")


@shared_task
def tarea_recordatorio_turno(turno_id):
    """
    Se programa con eta calculado al momento de crear el turno.
    Celery la ejecuta en el momento exacto, no antes.
    El email_service verifica internamente si el turno
    fue cancelado antes de mandar el mail.
    """
    from agenda.notifications.email_service import enviar_recordatorio_turno

    logger.info(f"Ejecutando recordatorio para turno {turno_id}")
    enviar_recordatorio_turno(turno_id)


@shared_task
def tarea_resumen_diario(medico_id):
    """
    Beat la ejecuta todos los días a la hora configurada
    en medico.hora_resumen_diario.
    Si el médico no tiene turnos hoy, el email_service
    manda igual un mail avisando que no hay turnos.
    """
    from agenda.notifications.email_service import enviar_resumen_diario

    logger.info(f"Ejecutando resumen diario para médico {medico_id}")
    enviar_resumen_diario(medico_id)
