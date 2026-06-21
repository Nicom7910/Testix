# Resumen de pruebas automatizadas

Se incorporaron pruebas automatizadas al sistema de reserva de canchas de tenis con el objetivo de validar funcionalidades críticas y mejorar la trazabilidad técnica del proyecto.

## Pruebas de integración

Las pruebas de integración validan el comportamiento completo de los endpoints principales del sistema.

### Usuarios

Se validó:

- Login correcto.
- Login incorrecto.
- Registro de usuario.
- Rechazo de email repetido.
- Listado de usuarios como administrador.
- Bloqueo de acceso a usuarios sin rol administrador.
- Consulta de usuario propio.
- Bloqueo de consulta de usuarios ajenos.
- Modificación de usuario.
- Baja lógica de usuario.

### Canchas

Se validó:

- Listado de canchas.
- Consulta de cancha por ID.
- Rechazo de cancha inexistente.
- Consulta de canchas disponibles.
- Detección de horarios ocupados.
- Alta de cancha como administrador.
- Bloqueo de alta sin permisos.
- Rechazo de precios inválidos.
- Modificación de cancha.
- Modificación de precios.
- Baja lógica de cancha.

### Reservas

Se validó:

- Listado de reservas como administrador.
- Bloqueo de listado sin permisos.
- Consulta de reservas activas, pendientes e historial.
- Creación correcta de reserva.
- Rechazo de usuario inexistente.
- Rechazo de cancha inexistente.
- Rechazo de cancha deshabilitada.
- Rechazo de reservas superpuestas.
- Rechazo de reservas con fecha pasada.
- Rechazo de horario de inicio mayor o igual al horario de fin.
- Pago correcto de seña.
- Rechazo de tarjeta inválida.
- Rechazo de tarjeta vencida.
- Rechazo de pago simulado.
- Cancelación con motivo.
- Rechazo de cancelación sin motivo.
- Bloqueo de cancelación sin permisos.

### Reportes

Se validó:

- Generación de reporte general como administrador.
- Bloqueo de reporte para usuario común.
- Rechazo de administrador inexistente.
- Filtro de reportes por fecha.
- Rechazo de rango de fechas inválido.
- Reporte sin reservas en el período.
- Cálculo de ingresos y señas.
- Ocupación por cancha.
- Detalle de reservas.

## Pruebas unitarias

Se validaron funciones internas relacionadas con:

- Cálculo de intervalos horarios.
- Manejo de reservas que terminan a medianoche.
- Detección de superposición.
- Validación de fecha y horario.
- Rechazo de fecha pasada.
- Rechazo de horarios fuera de rango.
- Cálculo de importes diurnos.
- Cálculo de importes nocturnos.
- Cálculo mixto diurno/nocturno.
- Validación de datos de pago.
- Rechazo de tarjeta inválida.
- Rechazo de titular vacío.
- Rechazo de vencimiento inválido.
- Rechazo de tarjeta vencida.
- Rechazo de código de seguridad inválido.

## Comandos utilizados

```bash
python -m pytest
```
