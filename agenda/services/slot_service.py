from datetime import datetime, timedelta
from django.utils import timezone

from agenda.models import Slot, DisponibilidadSemanal


def generar_slots_para_medico(medico, dias_adelante=30, dias_seleccionados=None):
    """Genera los slots de un médico para la ventana [hoy+1, hoy+dias_adelante].

    - Recorre las disponibilidades semanales activas del médico.
    - Cada slot dura `medico.tiempo_consulta` minutos.
    - `dias_seleccionados` (opcional) limita los días de la semana a generar.
    - Usa `get_or_create` para no duplicar slots existentes.
    - Retorna la cantidad de slots nuevos creados.
    """
    hoy = timezone.localdate()
    fecha_limite = hoy + timedelta(days=dias_adelante)

    slots_creados = 0
    fecha_actual = hoy

    while fecha_actual <= fecha_limite:
        fecha_actual += timedelta(days=1)
        weekday = fecha_actual.weekday()

        if dias_seleccionados is not None and weekday not in dias_seleccionados:
            continue

        disponibilidades = DisponibilidadSemanal.objects.filter(
            medico=medico, dias_semana=weekday, activo=True
        )

        for disponibilidad in disponibilidades:
            hora_actual = disponibilidad.hora_inicio
            duracion = medico.tiempo_consulta

            inicio_datetime = datetime.combine(fecha_actual, hora_actual)
            fin_disponobilidad = datetime.combine(fecha_actual, disponibilidad.hora_fin)

            while inicio_datetime + timedelta(minutes=duracion) <= fin_disponobilidad:
                hora_fin = inicio_datetime + timedelta(minutes=duracion)

                _, created = Slot.objects.get_or_create(
                    medico=medico,
                    fecha=fecha_actual,
                    hora_inicio=inicio_datetime.time(),
                    defaults={"hora_fin": hora_fin.time(), "disponible": True},
                )
                if created:
                    slots_creados += 1
                inicio_datetime += timedelta(minutes=duracion)

    return slots_creados