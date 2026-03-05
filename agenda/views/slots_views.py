from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from agenda.models import Medico
from agenda.services.slot_service import generar_slots_para_medico


# @login_required
def generar_agenda(request, medico_id):
    medico = get_object_or_404(Medico, id=medico_id)

    if request.method == "POST":
        generar_slots_para_medico(medico)
        messages.success(
            request, f"Agenda de 30 días generada para el Dr. {medico.apellido}"
        )
        return redirect("agenda:agenda_medico", medico_id=medico.id)

    return render(
        request, "agenda/medicos/confirmar_generacion.html", {"medico": medico}
    )
