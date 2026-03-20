from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django import forms
from agenda.models import TokenVerificacion
from agenda.utils import user_es_medico, user_es_secretaria
from django.contrib.auth.decorators import login_required


class EstablecerContrasenaForm(forms.Form):
    """Form contraseña usuario primera vez al activar cuenta"""

    password1 = forms.CharField(
        label="Contraseña",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        """Método que Django llama para validar
        el formulario completo."""
        cleaned_data = super().clean()

        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(
                "Las contraseñas no son iguales, por favor reescribalas."
            )

        return cleaned_data


def activar_cuenta(request, token):
    """
    Vista que recibe el token del link del mail.
    Verifica que exista, que sea de tipo activación,
    y que no haya expirado.
    Si todo está bien muestra el formulario de contraseña.
    """
    try:
        token_obj = TokenVerificacion.objects.select_related("usuario").get(
            token=token,
            tipo=TokenVerificacion.TIPO_ACTIVACION,
        )
    except TokenVerificacion.DoesNotExist:
        return render(request, "agenda/registro/token_invalido.html")

    if token_obj.esta_expirado():  # si expiro, se elimina ya no sirve
        token_obj.delete()
        return render(request, "agenda/registro/token_expirado.html")

    usuario = token_obj.usuario

    if request.method == "POST":
        form = EstablecerContrasenaForm(request.POST)
        if form.is_valid():
            # set_password hashea la contraseña
            usuario.set_password(form.cleaned_data["password1"])
            usuario.is_active = True
            usuario.save()
            token_obj.delete()

            if not user_es_medico(usuario) and not user_es_secretaria(usuario):
                from agenda.notifications.email_service import (
                    enviar_aviso_usuario_sin_rol,
                )

                enviar_aviso_usuario_sin_rol(usuario)

            messages.success(request, "Cuenta activada correctamente. Inicie sesión.")
            return redirect("login")

    else:
        form = EstablecerContrasenaForm()

    return render(
        request,
        "agenda/registro/activar_cuenta.html",
        {"form": form, "usuario": usuario},
    )


@login_required
def cuenta_pendiente(request):
    """
    Vista que ve el usuario sin rol mientras
    el admin completa su configuración.
    """
    # Si ya tiene rol no debería estar acá
    # lo mandamos al inicio
    if user_es_medico(request.user) or user_es_secretaria(request.user):
        return redirect("agenda:index")

    return render(request, "agenda/registro/cuenta_pendiente.html")


# RECUPERACION CUENTA EMAIL
class SolicitarRecuperacionForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )


def solicitar_recuperacion(request):
    """Vista donde el usuario ingresa su email.
    Si existe en la base de datos manda el mail con el link."""

    if request.method == "POST":
        form = SolicitarRecuperacionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]

            try:
                usuario = User.objects.get(email=email, is_active=True)

                TokenVerificacion.objects.filter(
                    usuario=usuario,
                    tipo=TokenVerificacion.TIPO_RECUPERACION,
                ).delete()

                token = TokenVerificacion.objects.create(
                    usuario=usuario,
                    tipo=TokenVerificacion.TIPO_RECUPERACION,
                )

                from agenda.notifications.email_service import (
                    enviar_recuperacion_contrasena,
                )

                enviar_recuperacion_contrasena(usuario, token)

            except User.DoesNotExist:
                pass

            messages.success(
                request,
                "Si ese mail esta registrado vas a recibir instrucciones para ingresar.",
            )
            return redirect("login")

    else:
        form = SolicitarRecuperacionForm()

    return render(
        request,
        "agenda/registro/solicitar_recuperacion.html",
        {"form": form},
    )


#
def recuperar_contrasena(request, token):
    """
    Vista que recibe el token del link mandado por el mail.
    Reutilizamos EstablecerContrasenaForm que ya existe.
    La lógica es casi idéntica a activar_cuenta pero
    no activa el usuario, solo cambia la contraseña.
    """
    try:
        token_obj = TokenVerificacion.objects.select_related("usuario").get(
            token=token,
            tipo=TokenVerificacion.TIPO_RECUPERACION,
        )
    except TokenVerificacion.DoesNotExist:
        return render(request, "agenda/registro/token_invalido.html")

    if token_obj.esta_expirado():
        token_obj.delete()
        return render(request, "agenda/registro/token_expirado.html")

    usuario = token_obj.usuario

    if request.method == "POST":
        form = EstablecerContrasenaForm(request.POST)
        if form.is_valid():
            usuario.set_password(form.cleaned_data["password1"])
            usuario.save()
            token_obj.delete()

            messages.success(
                request,
                "Contraseña actualizada correctamente. Ya podés iniciar sesión.",
            )
            return redirect("login")
    else:
        form = EstablecerContrasenaForm()

    return render(
        request,
        "agenda/registro/recuperar_contrasena.html",
        {"form": form, "usuario": usuario},
    )
