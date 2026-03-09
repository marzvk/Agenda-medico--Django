# agenda/context_processors.py


def auth_perfil(request):
    if request.user.is_authenticated:
        return {
            "es_medico": hasattr(request.user, "perfil_medico"),
            "medico_actual": getattr(request.user, "perfil_medico", None),
        }
    return {"es_medico": False, "medico_actual": None}
