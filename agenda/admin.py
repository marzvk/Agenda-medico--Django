from django.contrib import admin

# Register your models here.
from .models import Medico, Paciente, Turno

admin.site.register([Medico, Paciente, Turno])
