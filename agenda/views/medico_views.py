from django.shortcuts import render, get_object_or_404
from agenda.models import Medico, Slot
from django.contrib.auth.decorators import login_required


def lista_medicos(request):
    medicos = Medico.objects.all()
    return render(request, "agenda/medicos/lista.html", {"medicos": medicos})


# @login_required
def agenda_medico(request, medico_id):
    medico = get_object_or_404(Medico, pk=medico_id)

    slots = (
        Slot.objects.filter(medico=medico)
        .select_related("turno")
        .order_by("fecha", "hora_inicio")
    )

    return render(
        request,
        "agenda/medicos/agenda_medico.html",
        {"medico": medico, "slots": slots},
    )
