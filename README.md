# MedAgenda

Sistema de gestión de turnos médicos con notificaciones automáticas por email.

> Demo disponible en: https://marzvk.pythonanywhere.com

> Usuario médico: `medico` / Contraseña: `demo1234`

> Usuario secretaria: `secretaria` / Contraseña: `demo1234`

> Las notificaciones por mail no funcionan en el entorno demo.

> Para probarlas seguí las instrucciones de instalación local.

---

## Arquitectura general

- Proyecto Django con una sola app `agenda` y módulo `notifications`.
- La lógica de negocio vive en `services/`, separada de modelos y vistas.
- Las notificaciones viven en `notifications/`, separadas del resto de la lógica.
- Configuración centralizada en `config/`.

---

## Modelo de turnos

- El médico define duración fija de consulta.
- Las disponibilidades semanales generan slots futuros automáticamente.
- Cada turno ocupa exactamente un slot.
- La disponibilidad se controla exclusivamente mediante el modelo Slot.
- Se aplica restricción estructural OneToOne entre Slot y Turno.
- La lógica de negocio se encuentra en `services/` (SlotService y TurnoService).
- Se garantiza consistencia mediante transacciones atómicas y bloqueo `select_for_update`.

---

## Sistema de notificaciones

- Al confirmar un turno el paciente recibe un mail de confirmación inmediato.
- El paciente recibe un recordatorio configurable X horas antes del turno.
- El médico recibe un resumen diario de su agenda a la hora que configure.
- Cada médico controla individualmente sus notificaciones desde su perfil.
- Las notificaciones se ejecutan de forma asíncrona mediante Celery y Redis.
- Celery Beat programa el resumen diario según la configuración de cada médico.
- El schedule de Beat se persiste en base de datos mediante `django-celery-beat`.
- Al crear o modificar un médico una signal actualiza automáticamente su tarea en Beat.
- El sistema requiere tres procesos simultáneos: `runserver`, `celery worker` y `celery beat`.

---

## Seguridad y autenticación

- RBAC: control de acceso basado en roles (Médicos y Secretarias).
- Los médicos solo acceden a sus propios pacientes y turnos.
- Protección a nivel de objeto con `PermissionDenied` en vistas de detalle y edición.
- Vista `editar_historia` exclusiva para médicos con inserción automática de fecha y hora.
- Los usuarios son creados por el administrador y reciben un mail de activación.
- El usuario elige su propia contraseña al activar la cuenta.
- El link de activación expira a las 72 horas.
- Los usuarios sin rol asignado son bloqueados por middleware hasta que el admin complete su perfil.
- La recuperación de contraseña genera un token con expiración de 1 hora.

---

## Roles del sistema

- **Administrador:** acceso total, gestiona usuarios y configuración del sistema.
- **Secretaria:** carga turnos, gestiona pacientes, genera slots y agenda.
- **Médico:** accede solo a su propia agenda, pacientes y puede editar historias clínicas.

---

## Instalación local

Clonar el repositorio:
```bash
git clone https://github.com/marzvk/Agenda-medico--Django.git
cd Agenda-medico--Django
```

> Las instrucciones asumen Linux/Ubuntu. En Windows reemplazás `source .venv/bin/activate` por `.venv\Scripts\activate`.

Crear el entorno virtual e instalar dependencias:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crear el archivo `.env` en la raíz del proyecto:
```
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
SECRET_KEY=cualquier-clave-para-desarrollo
BASE_URL=http://127.0.0.1:8000
EMAIL_HOST_USER=tu_cuenta@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password
```

`EMAIL_HOST_PASSWORD` no es tu contraseña de Gmail sino una contraseña de aplicación generada por Google. Para obtenerla:

1. Entrás a myaccount.google.com
2. Seguridad → Verificación en dos pasos (tiene que estar activada)
3. Contraseñas de aplicaciones
4. Seleccionás "Correo" y "Otro dispositivo", escribís "MedAgenda"
5. Google genera una contraseña de 16 caracteres que pegás acá

Aplicar las migraciones:
```bash
python manage.py migrate
```

Crear el superusuario:
```bash
python manage.py createsuperuser
```

Crear el grupo Secretaria desde el admin de Django en `Autenticación y Autorización → Grupos`.

Instalar y levantar Redis:
```bash
# Ubuntu
sudo apt install redis-server
sudo systemctl start redis

# Verificar que funciona
redis-cli ping
```

---

## Correr el sistema

El sistema requiere tres procesos simultáneos en terminales separadas:
```bash
# Terminal 1
python manage.py runserver

# Terminal 2
celery -A config worker --loglevel=info

# Terminal 3
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Stack

- Python / Django
- SQLite (desarrollo) / PostgreSQL (producción)
- Celery + Redis
- django-celery-beat