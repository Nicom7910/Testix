# Automatizaciones con Selenium - Testix

Esta carpeta contiene las pruebas automatizadas de interfaz realizadas con Selenium para el sistema de reserva de canchas.

## Objetivo

Validar flujos críticos del sistema desde la interfaz de usuario, generando evidencia mediante capturas de pantalla.

## Flujos automatizados

| Test                                   | Caso relacionado | Descripción                      |
| -------------------------------------- | ---------------- | -------------------------------- |
| `test_cp01_login_cliente_valido`       | CP01             | Login válido con usuario cliente |
| `test_cp03_login_administrador_valido` | CP03             | Login válido con administrador   |
| `test_cp05_registro_usuario_valido`    | CP05             | Registro válido de usuario       |

## Requisitos previos

Antes de ejecutar Selenium, deben estar levantados:

### Backend

```bash
uvicorn app.main:app --reload
```
