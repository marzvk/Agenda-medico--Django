from django.shortcuts import render, get_object_or_404
from agenda.models import Medico, Slot
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Max


def lista_medicos(request):
    hoy = timezone.now().date()

    medicos = Medico.objects.annotate(
        slots_libres=Count(
            "slots", filter=Q(slots__disponible=True, slots__fecha__gte=hoy)
        ),
        ultima_agenda=Max("slots__fecha"),
    ).order_by("apellido")

    return render(
        request, "agenda/medicos/lista.html", {"medicos": medicos, "hoy": hoy}
    )


# @login_required
def agenda_medico(request, medico_id):

    medico = get_object_or_404(Medico, pk=medico_id)

    semanas = int(request.GET.get("semanas", 1))

    hoy = date.today()
    fecha_limite = hoy + timedelta(weeks=semanas)

    slots = (
        Slot.objects.filter(medico=medico, fecha__gte=hoy, fecha__lte=fecha_limite)
        .select_related("turno")
        .order_by("fecha", "hora_inicio")
    )

    return render(
        request,
        "agenda/medicos/agenda_medico.html",
        {"medico": medico, "slots": slots, "semanas_actuales": str(semanas)},
    )
