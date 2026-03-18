from django.shortcuts import redirect
from django.urls import reverse
from agenda.utils import user_es_medico, user_es_secretaria, user_es_admin


class RolRequeridoMiddleware:
    """
    Verifica que todo usuario logueado tenga un rol definido.
    Si no tiene rol redirige a la vista de espera.


    __init__ recibe get_response que es la vista siguiente en la cadena.
    __call__ se ejecuta en cada request antes de llegar a la vista.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo verificamos usuarios logueados
        if request.user.is_authenticated:

            if request.path.startswith("/admin/"):
                return self.get_response(request)

            if request.path.startswith("/accounts/activar/"):
                return self.get_response(request)

            # Estas URLs están permitidas sin rol
            # para evitar loops de redirección
            urls_permitidas = [
                reverse("cuenta_pendiente"),
                reverse("login"),
                reverse("logout"),
            ]

            # Si la URL actual no está permitida
            # y el usuario no tiene rol, redirigimos
            if request.path not in urls_permitidas:
                if not self._tiene_rol(request.user):
                    return redirect("cuenta_pendiente")

        # Si todo está bien, seguimos al siguiente middleware o vista
        response = self.get_response(request)
        return response

    def _tiene_rol(self, user):
        """
        Retorna True si el usuario tiene algún rol definido.
        Admin, médico y secretaria tienen rol.
        Un usuario recién activado sin perfil no tiene rol.
        """
        return user_es_admin(user) or user_es_medico(user) or user_es_secretaria(user)
