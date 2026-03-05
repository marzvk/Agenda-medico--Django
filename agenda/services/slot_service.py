from datetime import datetime, timedelta
from django.utils import timezone

from agenda.models import Slot, DisponibilidadSemanal


from datetime import datetime, timedelta
from django.utils import timezone
from agenda.models import Slot, DisponibilidadSemanal


def generar_slots_para_medico(medico, dias_adelante=30):
    hoy = timezone.localdate()
    fecha_limite = hoy + timedelta(days=dias_adelante)

    fecha_actual = hoy

    while fecha_actual <= fecha_limite:
        fecha_actual += timedelta(days=1)
        weekday = fecha_actual.weekday()

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

                Slot.objects.get_or_create(
                    medico=medico,
                    fecha=fecha_actual,
                    hora_inicio=inicio_datetime.time(),
                    defaults={"hora_fin": hora_fin.time(), "disponible": True},
                )
                inicio_datetime += timedelta(minutes=duracion)
