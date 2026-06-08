import streamlit as st
import requests
import time
from datetime import date, datetime

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Reserva de Canchas de Tenis",
    layout="centered"
)

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "reserva_pendiente" not in st.session_state:
    st.session_state.reserva_pendiente = None

if "mensaje_pago" not in st.session_state:
    st.session_state.mensaje_pago = None

if "tipo_mensaje_pago" not in st.session_state:
    st.session_state.tipo_mensaje_pago = None


def formatear_vencimiento(valor):
    solo_numeros = ""

    for caracter in valor:
        if caracter.isdigit():
            solo_numeros += caracter

    solo_numeros = solo_numeros[:4]

    if len(solo_numeros) >= 3:
        return solo_numeros[:2] + "/" + solo_numeros[2:]

    return solo_numeros


def validar_datos_pago_completos(
    numero_tarjeta,
    nombre_titular,
    vencimiento,
    codigo_seguridad
):
    numero_limpio = numero_tarjeta.replace(" ", "").replace("-", "")
    codigo_limpio = codigo_seguridad.strip()

    numero_valido = numero_limpio.isdigit() and len(numero_limpio) == 16
    nombre_valido = nombre_titular.strip() != ""
    vencimiento_valido = len(vencimiento) == 5 and "/" in vencimiento
    codigo_valido = codigo_limpio.isdigit() and len(codigo_limpio) in [3, 4]

    return (
        numero_valido
        and nombre_valido
        and vencimiento_valido
        and codigo_valido
    )


def convertir_fecha_hora_reserva(reserva):
    try:
        fecha_reserva = datetime.strptime(reserva["fecha"], "%Y-%m-%d").date()
        hora_inicio = reserva["hora_inicio"][:5]
        hora_reserva = datetime.strptime(hora_inicio, "%H:%M").time()
        return datetime.combine(fecha_reserva, hora_reserva)
    except Exception:
        return datetime.min


def ordenar_reservas_cliente(reservas, criterio_orden):
    if criterio_orden == "Más próximas primero":
        return sorted(
            reservas,
            key=convertir_fecha_hora_reserva,
            reverse=False
        )

    return sorted(
        reservas,
        key=convertir_fecha_hora_reserva,
        reverse=True
    )


def mostrar_mensaje_cancelacion_y_esperar(respuesta):
    datos_respuesta = respuesta.json()

    mensaje = datos_respuesta.get(
        "mensaje",
        "Reserva cancelada correctamente"
    )

    tipo_reembolso = datos_respuesta.get("tipo_reembolso")

    contenedor_mensaje = st.empty()

    if tipo_reembolso == "sin_reembolso":
        contenedor_mensaje.warning(mensaje)
    elif tipo_reembolso == "con_reembolso":
        contenedor_mensaje.success(mensaje)
    elif tipo_reembolso == "sin_pago":
        contenedor_mensaje.info(mensaje)
    else:
        contenedor_mensaje.success(mensaje)

    time.sleep(5)
    st.rerun()


def login(email, password):
    return requests.post(
        f"{API_URL}/usuarios/login",
        json={
            "email": email,
            "password": password
        },
        timeout=5
    )


def registrar_usuario(nombre, apellido, email, telefono, password):
    return requests.post(
        f"{API_URL}/usuarios/",
        json={
            "nombre": nombre,
            "apellido": apellido,
            "email": email,
            "telefono": telefono,
            "password": password,
            "rol": "COMUN"
        },
        timeout=5
    )


def obtener_canchas_disponibles(fecha=None, hora_inicio=None, hora_fin=None):
    params = {}

    if fecha is not None and hora_inicio is not None and hora_fin is not None:
        params = {
            "fecha": str(fecha),
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin
        }

    respuesta = requests.get(
        f"{API_URL}/canchas/disponibles",
        params=params,
        timeout=5
    )
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_todas_las_canchas():
    respuesta = requests.get(
        f"{API_URL}/canchas/",
        timeout=5
    )
    respuesta.raise_for_status()
    return respuesta.json()


def crear_cancha(
    nombre,
    superficie,
    techada,
    precio_por_hora,
    precio_diurno,
    precio_nocturno,
    admin_id
):
    return requests.post(
        f"{API_URL}/canchas/",
        params={
            "admin_id": admin_id
        },
        json={
            "nombre": nombre,
            "tipo_superficie": superficie,
            "techada": techada,
            "precio_por_hora": precio_por_hora,
            "precio_diurno": precio_diurno,
            "precio_nocturno": precio_nocturno
        },
        timeout=5
    )


def modificar_cancha(
    cancha_id,
    nombre,
    superficie,
    techada,
    precio_por_hora,
    precio_diurno,
    precio_nocturno,
    activa,
    admin_id
):
    return requests.put(
        f"{API_URL}/canchas/{cancha_id}",
        params={
            "admin_id": admin_id
        },
        json={
            "nombre": nombre,
            "tipo_superficie": superficie,
            "techada": techada,
            "precio_por_hora": precio_por_hora,
            "precio_diurno": precio_diurno,
            "precio_nocturno": precio_nocturno,
            "activa": activa
        },
        timeout=5
    )


def eliminar_cancha(cancha_id, admin_id):
    return requests.delete(
        f"{API_URL}/canchas/{cancha_id}",
        params={
            "admin_id": admin_id
        },
        timeout=5
    )


def realizar_reserva(usuario_id, cancha_id, fecha_reserva, hora_inicio, hora_fin):
    return requests.post(
        f"{API_URL}/reservas/",
        json={
            "usuario_id": usuario_id,
            "cancha_id": cancha_id,
            "fecha": str(fecha_reserva),
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin
        },
        timeout=5
    )


def pagar_sena_reserva(
    reserva_id,
    numero_tarjeta,
    nombre_titular,
    vencimiento,
    codigo_seguridad
):
    return requests.put(
        f"{API_URL}/reservas/{reserva_id}/pagar",
        json={
            "numero_tarjeta": numero_tarjeta,
            "nombre_titular": nombre_titular,
            "vencimiento": vencimiento,
            "codigo_seguridad": codigo_seguridad
        },
        timeout=5
    )


def obtener_reservas_activas_usuario(usuario_id):
    respuesta = requests.get(
        f"{API_URL}/reservas/usuario/{usuario_id}/activas",
        timeout=5
    )
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_reservas_pendientes_usuario(usuario_id):
    respuesta = requests.get(
        f"{API_URL}/reservas/usuario/{usuario_id}/pendientes",
        timeout=5
    )
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_reservas_canceladas_usuario(usuario_id):
    respuesta = requests.get(
        f"{API_URL}/reservas/usuario/{usuario_id}/canceladas",
        timeout=5
    )
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_reservas_pasadas_usuario(usuario_id):
    respuesta = requests.get(
        f"{API_URL}/reservas/usuario/{usuario_id}/pasadas",
        timeout=5
    )
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_historial_reservas_usuario(usuario_id):
    respuesta = requests.get(
        f"{API_URL}/reservas/usuario/{usuario_id}/historial",
        timeout=5
    )
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_reservas_activas(admin_id):
    respuesta = requests.get(
        f"{API_URL}/reservas/activas",
        params={
            "admin_id": admin_id
        },
        timeout=5
    )
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_reservas_pendientes_admin(admin_id):
    respuesta = requests.get(
        f"{API_URL}/reservas/pendientes",
        params={
            "admin_id": admin_id
        },
        timeout=5
    )
    respuesta.raise_for_status()
    return respuesta.json()


def cancelar_reserva_usuario(reserva_id, usuario_id):
    return requests.put(
        f"{API_URL}/reservas/{reserva_id}/cancelar",
        params={
            "usuario_id_solicitante": usuario_id
        },
        json={
            "motivo_cancelacion": "Cancelada por el usuario"
        },
        timeout=5
    )


def cancelar_reserva_con_motivo(reserva_id, motivo, admin_id):
    return requests.put(
        f"{API_URL}/reservas/{reserva_id}/cancelar",
        params={
            "usuario_id_solicitante": admin_id
        },
        json={
            "motivo_cancelacion": motivo
        },
        timeout=5
    )


def obtener_reporte_general(admin_id, fecha_desde=None, fecha_hasta=None):
    params = {
        "admin_id": admin_id
    }

    if fecha_desde is not None:
        params["fecha_desde"] = str(fecha_desde)

    if fecha_hasta is not None:
        params["fecha_hasta"] = str(fecha_hasta)

    respuesta = requests.get(
        f"{API_URL}/reportes/general",
        params=params,
        timeout=5
    )
    respuesta.raise_for_status()
    return respuesta.json()


def mostrar_reserva(reserva):
    st.write(f"Reserva N° {reserva['id']}")
    st.write(f"Usuario ID: {reserva['usuario_id']}")
    st.write(f"Cancha ID: {reserva['cancha_id']}")
    st.write(f"Fecha: {reserva['fecha']}")
    st.write(f"Horario: {reserva['hora_inicio']} a {reserva['hora_fin']}")
    st.write(f"Estado reserva: {reserva['estado_reserva']}")
    st.write(f"Estado pago: {reserva['estado_pago']}")
    st.write(f"Cantidad de horas: {reserva['cantidad_horas']}")
    st.write(f"Monto total: ${reserva['monto_total']}")
    st.write(f"Seña 50%: ${reserva['sena']}")

    if reserva.get("motivo_cancelacion") is not None:
        st.write(f"Motivo cancelación: {reserva['motivo_cancelacion']}")

    if reserva.get("fecha_creacion") is not None:
        st.write(f"Fecha de creación: {reserva['fecha_creacion']}")

    if reserva.get("requiere_devolucion") == True:
        st.warning(
            f"Requiere devolución: ${reserva.get('monto_devolucion', 0)} | "
            f"Estado devolución: {reserva.get('estado_devolucion', 'pendiente')}"
        )


def mostrar_reportes_admin(usuario):
    st.header("Reportes")

    tipo_reporte = st.selectbox(
        "Seleccionar tipo de reporte",
        [
            "Reporte de reservas",
            "Reporte general"
        ],
        key="admin_tipo_reporte"
    )

    usar_filtro = st.checkbox(
        "Filtrar reportes por fecha",
        key="admin_reporte_usar_filtro"
    )

    fecha_desde = None
    fecha_hasta = None

    if usar_filtro:
        fecha_desde = st.date_input(
            "Fecha desde",
            value=date.today(),
            key="admin_reporte_fecha_desde"
        )

        fecha_hasta = st.date_input(
            "Fecha hasta",
            value=date.today(),
            key="admin_reporte_fecha_hasta"
        )

    if st.button("Generar reporte", key="btn_generar_reporte_admin"):
        try:
            reporte = obtener_reporte_general(
                usuario["id"],
                fecha_desde,
                fecha_hasta
            )
        except requests.exceptions.RequestException as error:
            try:
                st.error(error.response.json()["detail"])
            except Exception:
                st.error("No se pudo generar el reporte")
        else:
            if tipo_reporte == "Reporte de reservas":
                st.subheader("Reporte de reservas")

                detalle_reservas = reporte.get("detalle_reservas", [])

                if len(detalle_reservas) == 0:
                    st.info("No hay reservas para mostrar en el reporte.")
                else:
                    st.table(
                        [
                            {
                                "Cancha": reserva["cancha"],
                                "Fecha": reserva["fecha"],
                                "Horario": reserva["horario"],
                                "Cliente": reserva["cliente"],
                                "Estado reserva": reserva["estado_reserva"],
                                "Estado pago": reserva["estado_pago"],
                                "Monto total": reserva["monto_total"],
                                "Seña": reserva["seña"]
                            }
                            for reserva in detalle_reservas
                        ]
                    )

            if tipo_reporte == "Reporte general":
                resumen = reporte["resumen"]

                st.subheader("Resumen general")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total reservas", resumen["total_reservas"])

                with col2:
                    st.metric("Pendientes", resumen["reservas_pendientes"])

                with col3:
                    st.metric("% cancelación", f"{resumen['porcentaje_cancelacion']}%")

                col4, col5 = st.columns(2)

                with col4:
                    st.metric("Ingresos potenciales", f"${resumen['ingresos_potenciales']}")

                with col5:
                    st.metric("Ingresos cobrados", f"${resumen['ingresos_cobrados']}")

                col6, col7 = st.columns(2)

                with col6:
                    st.metric("Señas pendientes", f"${resumen['senas_pendientes']}")

                with col7:
                    st.metric(
                        "Devoluciones pendientes",
                        f"${resumen['devoluciones_pendientes']}"
                    )

                st.subheader("Reservas por estado")
                st.table(reporte["reservas_por_estado"])

                st.subheader("Pagos por estado")
                st.table(reporte["pagos_por_estado"])

                st.subheader("Ocupación por cancha")
                ocupacion = reporte["ocupacion_por_cancha"]

                if len(ocupacion) == 0:
                    st.info("No hay datos de ocupación para mostrar.")
                else:
                    st.table(ocupacion)

                st.subheader("Horarios más solicitados")
                horarios = reporte["horarios_mas_solicitados"]

                if len(horarios) == 0:
                    st.info("No hay horarios solicitados para mostrar.")
                else:
                    st.table(horarios)


HORARIOS_INICIO = [
    "08:00", "08:30",
    "09:00", "09:30",
    "10:00", "10:30",
    "11:00", "11:30",
    "12:00", "12:30",
    "13:00", "13:30",
    "14:00", "14:30",
    "15:00", "15:30",
    "16:00", "16:30",
    "17:00", "17:30",
    "18:00", "18:30",
    "19:00", "19:30",
    "20:00", "20:30",
    "21:00", "21:30",
    "22:00", "22:30",
    "23:00"
]

HORARIOS_FIN = [
    "08:30",
    "09:00", "09:30",
    "10:00", "10:30",
    "11:00", "11:30",
    "12:00", "12:30",
    "13:00", "13:30",
    "14:00", "14:30",
    "15:00", "15:30",
    "16:00", "16:30",
    "17:00", "17:30",
    "18:00", "18:30",
    "19:00", "19:30",
    "20:00", "20:30",
    "21:00", "21:30",
    "22:00", "22:30",
    "23:00",
    "00:00"
]

TIPOS_SUPERFICIE = [
    "Polvo de ladrillo",
    "Cemento",
    "Césped sintético"
]


if st.session_state.usuario is None:

    st.title("🎾 Reserva de Canchas")

    tab_login, tab_registro = st.tabs(["Iniciar sesión", "Registrarse"])

    with tab_login:
        st.subheader("Iniciar sesión")

        email = st.text_input("Email", key="login_email")

        password = st.text_input(
            "Contraseña",
            type="password",
            key="login_password"
        )

        if st.button("Ingresar", key="btn_ingresar"):
            if email == "" or password == "":
                st.warning("Debe completar email y contraseña")
            else:
                try:
                    respuesta = login(email, password)
                except requests.exceptions.RequestException:
                    st.error("No se pudo conectar con el servidor")
                else:
                    if respuesta.status_code == 200:
                        datos = respuesta.json()
                        st.session_state.usuario = datos["usuario"]
                        st.rerun()
                    else:
                        st.error("Email o contraseña incorrectos")

    with tab_registro:
        st.subheader("Registro de usuario")

        nombre = st.text_input("Nombre", key="registro_nombre")
        apellido = st.text_input("Apellido", key="registro_apellido")
        email_registro = st.text_input("Mail", key="registro_email")
        telefono = st.text_input("Teléfono", key="registro_telefono")

        password_registro = st.text_input(
            "Contraseña",
            type="password",
            key="registro_password"
        )

        if st.button("Registrarme", key="btn_registrarme"):
            if (
                nombre == ""
                or apellido == ""
                or email_registro == ""
                or telefono == ""
                or password_registro == ""
            ):
                st.warning("Debe completar todos los campos")
            else:
                try:
                    respuesta = registrar_usuario(
                        nombre,
                        apellido,
                        email_registro,
                        telefono,
                        password_registro
                    )
                except requests.exceptions.RequestException:
                    st.error("No se pudo conectar con el servidor")
                else:
                    if respuesta.status_code == 200:
                        st.success(
                            "Usuario registrado correctamente. Ahora podés iniciar sesión."
                        )
                    else:
                        try:
                            st.error(respuesta.json()["detail"])
                        except Exception:
                            st.error("Error al registrar usuario")

else:

    usuario = st.session_state.usuario

    if st.session_state.reserva_pendiente is not None:

        reserva = st.session_state.reserva_pendiente

        st.title("Pago de seña")

        st.info(
            f"Reserva N° {reserva['id']} | "
            f"Fecha: {reserva['fecha']} | "
            f"Horario: {reserva['hora_inicio']} a {reserva['hora_fin']} | "
            f"Total: ${reserva['monto_total']} | "
            f"Seña a pagar 50%: ${reserva['sena']}"
        )

        st.warning(
            "La seña debe pagarse dentro de las 24 horas posteriores a la creación de la reserva."
        )

        numero_tarjeta = st.text_input(
            "Número de tarjeta",
            max_chars=19,
            key="pago_numero_tarjeta"
        )

        nombre_titular = st.text_input(
            "Nombre del titular",
            key="pago_nombre_titular"
        )

        vencimiento_sin_formato = st.text_input(
            "Vencimiento",
            placeholder="MMAA",
            max_chars=5,
            key="pago_vencimiento_input"
        )

        vencimiento = formatear_vencimiento(vencimiento_sin_formato)

        if vencimiento != "":
            st.caption(f"Formato aplicado: {vencimiento}")

        codigo_seguridad = st.text_input(
            "Código de seguridad",
            type="password",
            max_chars=4,
            key="pago_codigo_seguridad"
        )

        datos_pago_completos = validar_datos_pago_completos(
            numero_tarjeta,
            nombre_titular,
            vencimiento,
            codigo_seguridad
        )

        if not datos_pago_completos:
            st.warning(
                "Completá correctamente todos los datos para habilitar el pago: "
                "tarjeta de 16 dígitos, titular, vencimiento MMAA y código de 3 o 4 dígitos."
            )

        if st.button(
            "Pagar seña",
            disabled=not datos_pago_completos,
            key="btn_pagar_sena"
        ):
            try:
                respuesta = pagar_sena_reserva(
                    reserva["id"],
                    numero_tarjeta,
                    nombre_titular,
                    vencimiento,
                    codigo_seguridad
                )
            except requests.exceptions.RequestException:
                st.error("No se pudo conectar con el servidor")
            else:
                if respuesta.status_code == 200:
                    st.session_state.mensaje_pago = (
                        "Pago aprobado correctamente. La reserva quedó confirmada."
                    )
                    st.session_state.tipo_mensaje_pago = "success"
                    st.session_state.reserva_pendiente = None
                    st.rerun()
                else:
                    try:
                        st.error(respuesta.json()["detail"])
                    except Exception:
                        st.error("Error al procesar el pago")

        if st.button("Volver sin pagar", key="btn_volver_sin_pagar"):
            st.session_state.mensaje_pago = (
                "Pago cancelado. La reserva continúa pendiente de pago."
            )
            st.session_state.tipo_mensaje_pago = "warning"
            st.session_state.reserva_pendiente = None
            st.rerun()

        st.stop()

    st.title("🎾 Sistema de Reservas")

    st.success(
        f"Bienvenido {usuario['nombre']} {usuario.get('apellido', '')} - Rol: {usuario['rol']}"
    )

    if st.session_state.mensaje_pago is not None:
        if st.session_state.tipo_mensaje_pago == "success":
            st.success(st.session_state.mensaje_pago)
        elif st.session_state.tipo_mensaje_pago == "warning":
            st.warning(st.session_state.mensaje_pago)
        else:
            st.info(st.session_state.mensaje_pago)

        if st.button("Cerrar mensaje", key="btn_cerrar_mensaje_pago"):
            st.session_state.mensaje_pago = None
            st.session_state.tipo_mensaje_pago = None
            st.rerun()

    if st.button("Cerrar sesión", key="btn_cerrar_sesion"):
        st.session_state.usuario = None
        st.session_state.reserva_pendiente = None
        st.session_state.mensaje_pago = None
        st.session_state.tipo_mensaje_pago = None
        st.rerun()

    st.divider()

    if usuario["rol"] == "ADMINISTRADOR":

        st.header("Panel de administrador")

        tab_canchas, tab_reservas, tab_reportes = st.tabs(
            [
                "Canchas disponibles",
                "Reservas",
                "Reportes"
            ]
        )

        with tab_canchas:

            st.subheader("Crear nueva cancha")

            nombre = st.text_input(
                "Nombre de la cancha",
                key="admin_nombre_cancha"
            )

            superficie = st.selectbox(
                "Tipo de superficie",
                TIPOS_SUPERFICIE,
                key="admin_superficie_cancha"
            )

            techada = st.checkbox(
                "Techada",
                key="admin_techada_cancha"
            )

            precio_base = st.number_input(
                "Precio base por hora",
                min_value=1,
                step=500,
                key="admin_precio_base_cancha"
            )

            precio_diurno = st.number_input(
                "Precio diurno por hora",
                min_value=1,
                step=500,
                value=int(precio_base),
                key="admin_precio_diurno_cancha"
            )

            precio_nocturno = st.number_input(
                "Precio nocturno por hora",
                min_value=1,
                step=500,
                value=int(precio_base * 1.2),
                key="admin_precio_nocturno_cancha"
            )

            if st.button("Crear cancha", key="btn_crear_cancha"):
                if nombre == "":
                    st.warning("Debe ingresar el nombre de la cancha")
                else:
                    try:
                        respuesta = crear_cancha(
                            nombre,
                            superficie,
                            techada,
                            precio_base,
                            precio_diurno,
                            precio_nocturno,
                            usuario["id"]
                        )
                    except requests.exceptions.RequestException:
                        st.error("No se pudo conectar con el servidor")
                    else:
                        if respuesta.status_code == 200:
                            st.success("Cancha creada correctamente")
                            st.rerun()
                        else:
                            try:
                                st.error(respuesta.json()["detail"])
                            except Exception:
                                st.error("Error al crear la cancha")

            st.divider()

            st.subheader("Canchas disponibles")

            try:
                canchas_admin = obtener_todas_las_canchas()
            except requests.exceptions.RequestException:
                st.error("No se pudieron cargar las canchas")
                canchas_admin = []

            canchas_disponibles_admin = []

            for cancha in canchas_admin:
                if cancha["activa"] == True:
                    canchas_disponibles_admin.append(cancha)

            if len(canchas_disponibles_admin) == 0:
                st.info("No hay canchas disponibles.")
            else:
                for cancha in canchas_disponibles_admin:
                    with st.container(border=True):
                        st.subheader(cancha["nombre"])

                        st.write("### Datos actuales")
                        st.write(f"Nombre: {cancha['nombre']}")
                        st.write(f"Superficie: {cancha['tipo_superficie']}")
                        st.write(f"Techada: {'Sí' if cancha['techada'] else 'No'}")
                        st.write(f"Precio base: ${cancha['precio_por_hora']}")
                        st.write(
                            f"Precio diurno: ${cancha.get('precio_diurno', cancha['precio_por_hora'])}"
                        )
                        st.write(
                            f"Precio nocturno: ${cancha.get('precio_nocturno', cancha['precio_por_hora'])}"
                        )
                        st.write("Estado: Activa")

                        st.write("### Modificar cancha")

                        nuevo_nombre = st.text_input(
                            "Nombre",
                            value=cancha["nombre"],
                            key=f"admin_editar_nombre_cancha_{cancha['id']}"
                        )

                        superficie_actual = cancha["tipo_superficie"]

                        if superficie_actual in TIPOS_SUPERFICIE:
                            indice_superficie = TIPOS_SUPERFICIE.index(superficie_actual)
                        else:
                            indice_superficie = 0

                        nueva_superficie = st.selectbox(
                            "Tipo de superficie",
                            TIPOS_SUPERFICIE,
                            index=indice_superficie,
                            key=f"admin_editar_superficie_cancha_{cancha['id']}"
                        )

                        nueva_techada = st.checkbox(
                            "Techada",
                            value=cancha["techada"],
                            key=f"admin_editar_techada_cancha_{cancha['id']}"
                        )

                        nuevo_precio_base = st.number_input(
                            "Precio base por hora",
                            min_value=1,
                            value=int(cancha["precio_por_hora"]),
                            step=500,
                            key=f"admin_editar_precio_base_cancha_{cancha['id']}"
                        )

                        nuevo_precio_diurno = st.number_input(
                            "Precio diurno por hora",
                            min_value=1,
                            value=int(
                                cancha.get(
                                    "precio_diurno",
                                    cancha["precio_por_hora"]
                                )
                            ),
                            step=500,
                            key=f"admin_editar_precio_diurno_cancha_{cancha['id']}"
                        )

                        nuevo_precio_nocturno = st.number_input(
                            "Precio nocturno por hora",
                            min_value=1,
                            value=int(
                                cancha.get(
                                    "precio_nocturno",
                                    cancha["precio_por_hora"]
                                )
                            ),
                            step=500,
                            key=f"admin_editar_precio_nocturno_cancha_{cancha['id']}"
                        )

                        if st.button(
                            "Guardar cambios de cancha",
                            key=f"admin_guardar_cambios_cancha_{cancha['id']}"
                        ):
                            if nuevo_nombre.strip() == "":
                                st.warning("El nombre de la cancha no puede estar vacío")
                            else:
                                try:
                                    respuesta = modificar_cancha(
                                        cancha["id"],
                                        nuevo_nombre,
                                        nueva_superficie,
                                        nueva_techada,
                                        nuevo_precio_base,
                                        nuevo_precio_diurno,
                                        nuevo_precio_nocturno,
                                        True,
                                        usuario["id"]
                                    )
                                except requests.exceptions.RequestException:
                                    st.error("No se pudo conectar con el servidor")
                                else:
                                    if respuesta.status_code == 200:
                                        st.success("Cancha modificada correctamente")
                                        st.rerun()
                                    else:
                                        try:
                                            st.error(respuesta.json()["detail"])
                                        except Exception:
                                            st.error("Error al modificar la cancha")

                        if st.button(
                            "Dar de baja cancha",
                            key=f"admin_dar_baja_cancha_{cancha['id']}"
                        ):
                            try:
                                respuesta = eliminar_cancha(
                                    cancha["id"],
                                    usuario["id"]
                                )
                            except requests.exceptions.RequestException:
                                st.error("No se pudo conectar con el servidor")
                            else:
                                if respuesta.status_code == 200:
                                    st.success("Cancha dada de baja")
                                    st.rerun()
                                else:
                                    try:
                                        st.error(respuesta.json()["detail"])
                                    except Exception:
                                        st.error("Error al eliminar cancha")

        with tab_reservas:

            tab_reservas_activas_admin, tab_reservas_pendientes_admin = st.tabs(
                [
                    "Activas",
                    "Pendientes"
                ]
            )

            with tab_reservas_activas_admin:
                st.subheader("Reservas activas")

                try:
                    reservas_admin = obtener_reservas_activas(usuario["id"])
                except requests.exceptions.RequestException:
                    st.error("No se pudieron cargar las reservas activas")
                    reservas_admin = []

                if len(reservas_admin) == 0:
                    st.info("No hay reservas activas.")
                else:
                    for reserva in reservas_admin:
                        with st.container(border=True):
                            mostrar_reserva(reserva)

                            motivo = st.text_area(
                                "Motivo de cancelación",
                                key=f"admin_motivo_cancelacion_activa_{reserva['id']}"
                            )

                            if st.button(
                                "Cancelar reserva",
                                key=f"admin_cancelar_reserva_activa_{reserva['id']}"
                            ):
                                if motivo.strip() == "":
                                    st.warning("Debe ingresar un motivo de cancelación")
                                else:
                                    try:
                                        respuesta = cancelar_reserva_con_motivo(
                                            reserva["id"],
                                            motivo,
                                            usuario["id"]
                                        )
                                    except requests.exceptions.RequestException:
                                        st.error("No se pudo conectar con el servidor")
                                    else:
                                        if respuesta.status_code == 200:
                                            mostrar_mensaje_cancelacion_y_esperar(respuesta)
                                        else:
                                            try:
                                                st.error(respuesta.json()["detail"])
                                            except Exception:
                                                st.error("Error al cancelar la reserva")

            with tab_reservas_pendientes_admin:
                st.subheader("Reservas pendientes")

                try:
                    reservas_admin = obtener_reservas_pendientes_admin(usuario["id"])
                except requests.exceptions.RequestException:
                    st.error("No se pudieron cargar las reservas pendientes")
                    reservas_admin = []

                if len(reservas_admin) == 0:
                    st.info("No hay reservas pendientes.")
                else:
                    for reserva in reservas_admin:
                        with st.container(border=True):
                            mostrar_reserva(reserva)

                            motivo = st.text_area(
                                "Motivo de cancelación",
                                key=f"admin_motivo_cancelacion_pendiente_{reserva['id']}"
                            )

                            if st.button(
                                "Cancelar reserva pendiente",
                                key=f"admin_cancelar_reserva_pendiente_{reserva['id']}"
                            ):
                                if motivo.strip() == "":
                                    st.warning("Debe ingresar un motivo de cancelación")
                                else:
                                    try:
                                        respuesta = cancelar_reserva_con_motivo(
                                            reserva["id"],
                                            motivo,
                                            usuario["id"]
                                        )
                                    except requests.exceptions.RequestException:
                                        st.error("No se pudo conectar con el servidor")
                                    else:
                                        if respuesta.status_code == 200:
                                            mostrar_mensaje_cancelacion_y_esperar(respuesta)
                                        else:
                                            try:
                                                st.error(respuesta.json()["detail"])
                                            except Exception:
                                                st.error("Error al cancelar la reserva")

        with tab_reportes:
            mostrar_reportes_admin(usuario)

        st.stop()

    if usuario["rol"] == "COMUN":

        st.header("Mis reservas")

        criterio_orden_reservas = st.selectbox(
            "Ordenar reservas por fecha de reserva",
            [
                "Más próximas primero",
                "Más lejanas primero"
            ],
            key="cliente_orden_reservas"
        )

        tab_activas, tab_pendientes, tab_pasadas, tab_canceladas, tab_historial = st.tabs(
            [
                "Activas",
                "Pendientes",
                "Pasadas",
                "Canceladas",
                "Historial completo"
            ]
        )

        with tab_activas:
            try:
                reservas = obtener_reservas_activas_usuario(usuario["id"])
                reservas = ordenar_reservas_cliente(
                    reservas,
                    criterio_orden_reservas
                )
            except requests.exceptions.RequestException:
                st.error("No se pudieron cargar tus reservas activas")
                reservas = []

            if len(reservas) == 0:
                st.info("No tenés reservas activas.")
            else:
                for reserva in reservas:
                    with st.container(border=True):
                        mostrar_reserva(reserva)

                        if st.button(
                            "Cancelar reserva",
                            key=f"usuario_cancelar_reserva_{reserva['id']}"
                        ):
                            try:
                                respuesta = cancelar_reserva_usuario(
                                    reserva["id"],
                                    usuario["id"]
                                )
                            except requests.exceptions.RequestException:
                                st.error("No se pudo conectar con el servidor")
                            else:
                                if respuesta.status_code == 200:
                                    mostrar_mensaje_cancelacion_y_esperar(respuesta)
                                else:
                                    try:
                                        st.error(respuesta.json()["detail"])
                                    except Exception:
                                        st.error("Error al cancelar la reserva")

            st.divider()

            st.header("Canchas")

            st.subheader("Buscar disponibilidad")

            fecha_busqueda = st.date_input(
                "Fecha de reserva",
                value=date.today(),
                min_value=date.today(),
                key="buscar_fecha_reserva"
            )

            hora_inicio_busqueda = st.selectbox(
                "Hora de inicio",
                HORARIOS_INICIO,
                key="buscar_hora_inicio_reserva"
            )

            hora_fin_busqueda = st.selectbox(
                "Hora de fin",
                HORARIOS_FIN,
                key="buscar_hora_fin_reserva"
            )

            try:
                canchas = obtener_canchas_disponibles(
                    fecha_busqueda,
                    hora_inicio_busqueda,
                    hora_fin_busqueda
                )
            except requests.exceptions.RequestException as error:
                try:
                    st.error(error.response.json()["detail"])
                except Exception:
                    st.error("No se pudo conectar con el servidor")
                canchas = []

            if len(canchas) == 0:
                st.warning(
                    "No hay canchas disponibles para la fecha y horario seleccionados"
                )

            for cancha in canchas:

                with st.container(border=True):

                    st.subheader(cancha["nombre"])

                    st.write(f"Superficie: {cancha['tipo_superficie']}")
                    st.write(f"Techada: {'Sí' if cancha['techada'] else 'No'}")
                    st.write(
                        f"Precio diurno: ${cancha.get('precio_diurno', cancha['precio_por_hora'])}"
                    )
                    st.write(
                        f"Precio nocturno: ${cancha.get('precio_nocturno', cancha['precio_por_hora'])}"
                    )

                    st.write("### Reservar cancha")

                    st.write(f"Fecha seleccionada: {fecha_busqueda}")

                    st.write(
                        f"Horario seleccionado: "
                        f"{hora_inicio_busqueda} a {hora_fin_busqueda}"
                    )

                    col_guardar, col_pagar = st.columns(2)

                    with col_guardar:
                        if st.button(
                            "Guardar reserva",
                            key=(
                                f"usuario_guardar_reserva_"
                                f"{cancha['id']}_"
                                f"{fecha_busqueda}_"
                                f"{hora_inicio_busqueda}_"
                                f"{hora_fin_busqueda}"
                            )
                        ):
                            try:
                                respuesta = realizar_reserva(
                                    usuario["id"],
                                    cancha["id"],
                                    fecha_busqueda,
                                    hora_inicio_busqueda,
                                    hora_fin_busqueda
                                )
                            except requests.exceptions.RequestException:
                                st.error("No se pudo conectar con el servidor")
                            else:
                                if respuesta.status_code == 200:
                                    st.success(
                                        "Reserva guardada correctamente. El pago quedó pendiente."
                                    )
                                    st.rerun()
                                else:
                                    try:
                                        st.error(respuesta.json()["detail"])
                                    except Exception:
                                        st.error("Error al guardar la reserva")

                    with col_pagar:
                        if st.button(
                            "Pagar seña ahora",
                            key=(
                                f"usuario_pagar_reserva_"
                                f"{cancha['id']}_"
                                f"{fecha_busqueda}_"
                                f"{hora_inicio_busqueda}_"
                                f"{hora_fin_busqueda}"
                            )
                        ):
                            try:
                                respuesta = realizar_reserva(
                                    usuario["id"],
                                    cancha["id"],
                                    fecha_busqueda,
                                    hora_inicio_busqueda,
                                    hora_fin_busqueda
                                )
                            except requests.exceptions.RequestException:
                                st.error("No se pudo conectar con el servidor")
                            else:
                                if respuesta.status_code == 200:
                                    datos = respuesta.json()
                                    st.session_state.reserva_pendiente = datos
                                    st.rerun()
                                else:
                                    try:
                                        st.error(respuesta.json()["detail"])
                                    except Exception:
                                        st.error("Error al realizar la reserva")

        with tab_pendientes:
            try:
                reservas_pendientes = obtener_reservas_pendientes_usuario(usuario["id"])
                reservas_pendientes = ordenar_reservas_cliente(
                    reservas_pendientes,
                    criterio_orden_reservas
                )
            except requests.exceptions.RequestException:
                st.error("No se pudieron cargar tus reservas pendientes")
                reservas_pendientes = []

            if len(reservas_pendientes) == 0:
                st.info("No tenés reservas pendientes.")
            else:
                st.warning(
                    "Recordá que la seña debe pagarse dentro de las 24 horas posteriores a la creación de la reserva."
                )

                for reserva in reservas_pendientes:
                    with st.container(border=True):
                        mostrar_reserva(reserva)

                        if st.button(
                            "Pagar seña pendiente",
                            key=f"usuario_pagar_reserva_pendiente_{reserva['id']}"
                        ):
                            st.session_state.reserva_pendiente = reserva
                            st.rerun()

                        if st.button(
                            "Cancelar reserva pendiente",
                            key=f"usuario_cancelar_reserva_pendiente_{reserva['id']}"
                        ):
                            try:
                                respuesta = cancelar_reserva_usuario(
                                    reserva["id"],
                                    usuario["id"]
                                )
                            except requests.exceptions.RequestException:
                                st.error("No se pudo conectar con el servidor")
                            else:
                                if respuesta.status_code == 200:
                                    mostrar_mensaje_cancelacion_y_esperar(respuesta)
                                else:
                                    try:
                                        st.error(respuesta.json()["detail"])
                                    except Exception:
                                        st.error("Error al cancelar la reserva")

        with tab_pasadas:
            try:
                reservas_pasadas = obtener_reservas_pasadas_usuario(usuario["id"])
                reservas_pasadas = ordenar_reservas_cliente(
                    reservas_pasadas,
                    criterio_orden_reservas
                )
            except requests.exceptions.RequestException:
                st.error("No se pudieron cargar tus reservas pasadas")
                reservas_pasadas = []

            if len(reservas_pasadas) == 0:
                st.info("No tenés reservas pasadas.")
            else:
                for reserva in reservas_pasadas:
                    with st.container(border=True):
                        mostrar_reserva(reserva)

        with tab_canceladas:
            try:
                reservas_canceladas = obtener_reservas_canceladas_usuario(usuario["id"])
                reservas_canceladas = ordenar_reservas_cliente(
                    reservas_canceladas,
                    criterio_orden_reservas
                )
            except requests.exceptions.RequestException:
                st.error("No se pudieron cargar tus reservas canceladas")
                reservas_canceladas = []

            if len(reservas_canceladas) == 0:
                st.info("No tenés reservas canceladas.")
            else:
                for reserva in reservas_canceladas:
                    with st.container(border=True):
                        mostrar_reserva(reserva)

        with tab_historial:
            try:
                historial = obtener_historial_reservas_usuario(usuario["id"])
                historial = ordenar_reservas_cliente(
                    historial,
                    criterio_orden_reservas
                )
            except requests.exceptions.RequestException:
                st.error("No se pudo cargar tu historial")
                historial = []

            if len(historial) == 0:
                st.info("No hay reservas en tu historial.")
            else:
                for reserva in historial:
                    with st.container(border=True):
                        mostrar_reserva(reserva)