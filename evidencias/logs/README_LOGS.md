# Evidencias de logs

Esta carpeta contiene fragmentos representativos de logs generados por el sistema durante la ejecución de pruebas funcionales.

## Objetivo

El objetivo de estas evidencias es demostrar que el sistema registra eventos importantes para analizar errores, validar flujos críticos y respaldar el proceso de testing.

## Archivos incluidos

| Archivo                     | Descripción                                                                             |
| --------------------------- | --------------------------------------------------------------------------------------- |
| `BUG_LOGIN_Y_RESERVA.log`   | Evidencia del login de usuario y creación de una reserva válida.                        |
| `BUG_PAGO_SENA.log`         | Evidencia del pago de seña y cambio de estado de la reserva.                            |
| `BUG_CONSULTA_RESERVAS.log` | Evidencia de consulta de reservas activas, pendientes, pasadas, canceladas e historial. |

## Eventos registrados

Los logs permiten analizar:

- Intentos de login exitosos y rechazados.
- Creación de reservas.
- Validación de cancha activa.
- Validación de fecha y horario.
- Cálculo de importe total y seña.
- Validación de superposición de reservas.
- Pago de seña.
- Cambio de estado de reservas.
- Consulta de historial del usuario.

## Ubicación del log original

Durante la ejecución del sistema, el log completo se genera en:

```txt
logs/sistema.log
```
