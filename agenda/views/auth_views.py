from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django import forms
from agenda.models import TokenVerificacion


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
