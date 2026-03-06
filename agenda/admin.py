from django.contrib import admin

# Register your models here.
from .models import Medico, Paciente, Turno, Slot, DisponibilidadSemanal

admin.site.register([Medico, Paciente, Turno, Slot, DisponibilidadSemanal])
