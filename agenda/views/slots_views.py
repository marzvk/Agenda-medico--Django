from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from agenda.models import Medico, Slot, DisponibilidadSemanal
from agenda.services.slot_service import generar_slots_para_medico
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta, datetime, time
from django.db import transaction
from django.core.exceptions import PermissionDenied


#
@login_required
def generar_agenda(request, medico_id):
    # Solo secretaria puede generar agenda
    if hasattr(request.user, "perfil_medico"):
        raise PermissionDenied
    medico = get_object_or_404(Medico, id=medico_id)
    hoy = timezone.localdate()

    if request.method == "POST":

        fecha_eliminar = request.POST.get("fecha_eliminar")
        if fecha_eliminar:

            slots_a_borrar = Slot.objects.filter(
                medico=medico, fecha=fecha_eliminar, disponible=True
            )
            cantidad = slots_a_borrar.count()
            slots_a_borrar.delete()
            messages.success(
                request, f"Se han eliminado {cantidad} slots del día {fecha_eliminar}."
            )
            return redirect("agenda:generar_agenda", medico_id=medico.id)

        semanas = int(request.POST.get("semanas", 4))
        dias_seleccionados = request.POST.getlist("dias_seleccionados")
        modo = request.POST.get("modo")

        dias_indices = [int(d) for d in dias_seleccionados]

        fecha_inicio = hoy + timedelta(days=1)
        fecha_fin = hoy + timedelta(weeks=semanas)

        with transaction.atomic():

            if modo == "reemplazar":
                Slot.objects.filter(
                    medico=medico,
                    fecha__range=[fecha_inicio, fecha_fin],
                    disponible=True,
                ).delete()

            disponibilidades = medico.disponibilidades.filter(
                activo=True, dias_semana__in=dias_indices
            )

            slots_creados = 0
            fecha_cursor = fecha_inicio
            while fecha_cursor <= fecha_fin:

                dia_semana_cursor = fecha_cursor.weekday()

                if dia_semana_cursor in dias_indices:

                    bloques_dia = disponibilidades.filter(dias_semana=dia_semana_cursor)
                    duracion = medico.tiempo_consulta

                    for bloque in bloques_dia:

                        hora_actual = bloque.hora_inicio
                        while hora_actual < bloque.hora_fin:

                            proxima_hora_dt = timezone.datetime.combine(
                                fecha_cursor, hora_actual
                            ) + timedelta(minutes=duracion)
                            proxima_hora = proxima_hora_dt.time()

                            if (
                                proxima_hora > bloque.hora_fin
                                and hora_actual < bloque.hora_fin
                            ):

                                break

                            slot, created = Slot.objects.get_or_create(
                                medico=medico,
                                fecha=fecha_cursor,
                                hora_inicio=hora_actual,
                                hora_fin=proxima_hora,
                                defaults={"disponible": True},
                            )
                            if created:
                                slots_creados += 1

                            full_datetime = timezone.datetime.combine(
                                fecha_cursor, hora_actual
                            ) + timedelta(minutes=duracion)
                            hora_actual = full_datetime.time()

                fecha_cursor += timedelta(days=1)

        messages.success(
            request, f"Proceso finalizado. Se crearon {slots_creados} nuevos turnos."
        )
        return redirect("agenda:generar_agenda", medico_id=medico.id)

    dias_con_agenda = (
        Slot.objects.filter(medico=medico, fecha__gte=hoy)
        .values("fecha")
        .annotate(
            total_slots=Count("id"), ocupados=Count("id", filter=Q(disponible=False))
        )
        .order_by("fecha")
    )

    configuracion_actual = medico.disponibilidades.filter(activo=True).order_by(
        "dias_semana", "hora_inicio"
    )
    dias_trabajo_ids = list(configuracion_actual.values_list("dias_semana", flat=True))

    context = {
        "medico": medico,
        "dias_con_agenda": dias_con_agenda,
        "dias_trabajo_ids": dias_trabajo_ids,
        "configuracion_actual": configuracion_actual,
        "hoy": hoy,
        "dias_nombres": DisponibilidadSemanal.DIAS_SEMANA,
    }
    return render(request, "agenda/medicos/generar_agenda.html", context)


# SLOT INDIVIDUAL


@login_required
def crear_slot_manual(request, medico_id):
    from agenda.utils import user_es_medico

    if user_es_medico(request.user):
        if request.user.perfil_medico.id != medico_id:
            raise PermissionDenied

    medico = get_object_or_404(Medico, id=medico_id)

    if request.method == "POST":
        fecha = request.POST.get("fecha")
        h_inicio = request.POST.get("hora_inicio")
        h_fin = request.POST.get("hora_fin")

        # Validar superposición
        existe_choque = Slot.objects.filter(
            medico=medico, fecha=fecha, hora_inicio__lt=h_fin, hora_fin__gt=h_inicio
        ).exists()

        if existe_choque:
            messages.error(
                request, "Error: Ya existe un turno que se superpone con este horario."
            )
        else:
            try:
                Slot.objects.create(
                    medico=medico,
                    fecha=fecha,
                    hora_inicio=h_inicio,
                    hora_fin=h_fin,
                    disponible=True,
                )
                messages.success(request, "Slot individual creado con éxito.")
            except Exception as e:
                messages.error(request, f"Error al crear el slot: {e}")

    return redirect("agenda:generar_agenda", medico_id=medico.id)
