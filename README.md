##El sistema utiliza una arquitectura basada en Slots.

-El médico define duración fija de consulta.

-Las disponibilidades semanales generan slots futuros automáticamente.

-Cada turno ocupa exactamente un slot.

-No existe validación de solapamiento en Turno.

-La disponibilidad se controla exclusivamente mediante el modelo Slot.

-La lógica de negocio se encuentra en services (SlotService y TurnoService).