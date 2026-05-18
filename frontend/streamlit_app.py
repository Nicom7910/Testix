import streamlit as st
import requests
from datetime import date

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Reserva de Canchas de Tenis",
    layout="centered"
)

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "reserva_pendiente" not in st.session_state:
    st.session_state.reserva_pendiente = None


def login(email, password):
    return requests.post(
        f"{API_URL}/usuarios/login",
        json={"email": email, "password": password},
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


def obtener_canchas_disponibles():
    respuesta = requests.get(f"{API_URL}/canchas/disponibles", timeout=5)
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_todas_las_canchas():
    respuesta = requests.get(f"{API_URL}/canchas/", timeout=5)
    respuesta.raise_for_status()
    return respuesta.json()


def crear_cancha(nombre, superficie, techada, precio):
    return requests.post(
        f"{API_URL}/canchas/",
        json={
            "nombre": nombre,
            "tipo_superficie": superficie,
            "techada": techada,
            "precio_por_hora": precio
        },
        timeout=5
    )


def eliminar_cancha(cancha_id):
    return requests.delete(f"{API_URL}/canchas/{cancha_id}", timeout=5)


def modificar_precio_cancha(cancha_id, precio):
    return requests.patch(
        f"{API_URL}/canchas/{cancha_id}/precio",
        params={"precio_por_hora": precio},
        timeout=5
    )


def realizar_reserva(usuario_id, cancha_id, fecha, hora_inicio, hora_fin):
    return requests.post(
        f"{API_URL}/reservas/",
        json={
            "usuario_id": usuario_id,
            "cancha_id": cancha_id,
            "fecha": str(fecha),
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


def obtener_reservas_activas():
    respuesta = requests.get(
        f"{API_URL}/reservas/activas",
        timeout=5
    )
    respuesta.raise_for_status()
    return respuesta.json()


def cancelar_reserva_usuario(reserva_id):
    return requests.put(
        f"{API_URL}/reservas/{reserva_id}/cancelar",
        json={
            "motivo_cancelacion": "Cancelada por el usuario"
        },
        timeout=5
    )


def cancelar_reserva_con_motivo(reserva_id, motivo):
    return requests.put(
        f"{API_URL}/reservas/{reserva_id}/cancelar",
        json={
            "motivo_cancelacion": motivo
        },
        timeout=5
    )


HORARIOS = [
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

        if st.button("Ingresar"):
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

        if st.button("Registrarme"):
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
            f"Total: ${reserva['monto_total']} | "
            f"Seña a pagar 50%: ${reserva['sena']}"
        )

        numero_tarjeta = st.text_input("Número de tarjeta")
        nombre_titular = st.text_input("Nombre del titular")
        vencimiento = st.text_input("Vencimiento", placeholder="MM/AA")
        codigo_seguridad = st.text_input(
            "Código de seguridad",
            type="password"
        )

        datos_completos = (
            numero_tarjeta.strip() != ""
            and nombre_titular.strip() != ""
            and vencimiento.strip() != ""
            and codigo_seguridad.strip() != ""
        )

        if not datos_completos:
            st.warning("Complete todos los datos para habilitar el pago")

        if st.button("Pagar seña", disabled=not datos_completos):
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
                    st.success(
                        "Pago realizado correctamente. La reserva quedó activa."
                    )
                    st.session_state.reserva_pendiente = None
                    st.rerun()
                else:
                    try:
                        st.error(respuesta.json()["detail"])
                    except Exception:
                        st.error("Error al procesar el pago")

        if st.button("Cancelar operación"):
            st.session_state.reserva_pendiente = None
            st.rerun()

        st.stop()

    st.title("🎾 Sistema de Reservas")

    st.success(
        f"Bienvenido {usuario['nombre']} {usuario.get('apellido', '')} - Rol: {usuario['rol']}"
    )

    if st.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.session_state.reserva_pendiente = None
        st.rerun()

    st.divider()

    if usuario["rol"] == "ADMINISTRADOR":

        st.header("Panel de administrador")

        nombre = st.text_input("Nombre de la cancha")

        superficie = st.selectbox(
            "Tipo de superficie",
            [
                "Polvo de ladrillo",
                "Cemento",
                "Césped sintético"
            ]
        )

        techada = st.checkbox("Techada")

        precio = st.number_input(
            "Precio por hora",
            min_value=1,
            step=500
        )

        if st.button("Crear cancha"):
            if nombre == "":
                st.warning("Debe ingresar el nombre de la cancha")
            else:
                try:
                    respuesta = crear_cancha(nombre, superficie, techada, precio)
                except requests.exceptions.RequestException:
                    st.error("No se pudo conectar con el servidor")
                else:
                    if respuesta.status_code == 200:
                        st.success("Cancha creada correctamente")
                        st.rerun()
                    else:
                        st.error("Error al crear la cancha")

        st.divider()

        st.header("Reservas activas")

        try:
            reservas_activas = obtener_reservas_activas()
        except requests.exceptions.RequestException:
            st.error("No se pudieron cargar las reservas activas")
            reservas_activas = []

        if len(reservas_activas) == 0:
            st.info("No hay reservas activas.")
        else:
            for reserva in reservas_activas:
                with st.container(border=True):
                    st.write(f"Reserva N° {reserva['id']}")
                    st.write(f"Usuario ID: {reserva['usuario_id']}")
                    st.write(f"Cancha ID: {reserva['cancha_id']}")
                    st.write(f"Fecha: {reserva['fecha']}")
                    st.write(
                        f"Horario: {reserva['hora_inicio']} a {reserva['hora_fin']}"
                    )
                    st.write(f"Cantidad de horas: {reserva['cantidad_horas']}")
                    st.write(f"Monto total: ${reserva['monto_total']}")
                    st.write(f"Seña 50%: ${reserva['sena']}")

                    motivo = st.text_area(
                        "Motivo de cancelación",
                        key=f"motivo_cancelacion_{reserva['id']}"
                    )

                    if st.button(
                        "Cancelar reserva",
                        key=f"admin_cancelar_reserva_{reserva['id']}"
                    ):
                        if motivo.strip() == "":
                            st.warning("Debe ingresar un motivo de cancelación")
                        else:
                            try:
                                respuesta = cancelar_reserva_con_motivo(
                                    reserva["id"],
                                    motivo
                                )
                            except requests.exceptions.RequestException:
                                st.error("No se pudo conectar con el servidor")
                            else:
                                if respuesta.status_code == 200:
                                    st.success("Reserva cancelada correctamente")
                                    st.rerun()
                                else:
                                    try:
                                        st.error(respuesta.json()["detail"])
                                    except Exception:
                                        st.error("Error al cancelar la reserva")

        st.divider()

    if usuario["rol"] == "COMUN":

        st.header("Mis reservas activas")

        try:
            reservas = obtener_reservas_activas_usuario(usuario["id"])
        except requests.exceptions.RequestException:
            st.error("No se pudieron cargar tus reservas")
            reservas = []

        if len(reservas) == 0:
            st.info("No tenés reservas activas.")
        else:
            for reserva in reservas:
                with st.container(border=True):
                    st.write(f"Reserva N° {reserva['id']}")
                    st.write(f"Cancha ID: {reserva['cancha_id']}")
                    st.write(f"Fecha: {reserva['fecha']}")
                    st.write(
                        f"Horario: {reserva['hora_inicio']} a {reserva['hora_fin']}"
                    )
                    st.write(f"Cantidad de horas: {reserva['cantidad_horas']}")
                    st.write(f"Monto total: ${reserva['monto_total']}")
                    st.write(f"Seña 50%: ${reserva['sena']}")

                    if st.button(
                        "Cancelar reserva",
                        key=f"cancelar_{reserva['id']}"
                    ):
                        try:
                            respuesta = cancelar_reserva_usuario(reserva["id"])
                        except requests.exceptions.RequestException:
                            st.error("No se pudo conectar con el servidor")
                        else:
                            if respuesta.status_code == 200:
                                st.success("Reserva cancelada correctamente")
                                st.rerun()
                            else:
                                st.error("Error al cancelar la reserva")

        st.divider()

    st.header("Canchas")

    try:
        if usuario["rol"] == "ADMINISTRADOR":
            canchas = obtener_todas_las_canchas()
        else:
            canchas = obtener_canchas_disponibles()

    except requests.exceptions.RequestException:
        st.error("No se pudo conectar con el servidor")
        canchas = []

    if len(canchas) == 0:
        st.warning("No hay canchas cargadas")

    for cancha in canchas:

        with st.container(border=True):

            st.subheader(cancha["nombre"])

            st.write(f"Superficie: {cancha['tipo_superficie']}")
            st.write(f"Techada: {'Sí' if cancha['techada'] else 'No'}")
            st.write(f"Precio por hora: ${cancha['precio_por_hora']}")

            if usuario["rol"] == "ADMINISTRADOR":

                st.write(f"Estado: {'Activa' if cancha['activa'] else 'Inactiva'}")

                nuevo_precio = st.number_input(
                    "Nuevo precio por hora",
                    min_value=1,
                    value=int(cancha["precio_por_hora"]),
                    step=500,
                    key=f"nuevo_precio_{cancha['id']}"
                )

                if st.button(
                    "Modificar precio",
                    key=f"modificar_precio_{cancha['id']}"
                ):
                    try:
                        respuesta = modificar_precio_cancha(
                            cancha["id"],
                            nuevo_precio
                        )
                    except requests.exceptions.RequestException:
                        st.error("No se pudo conectar con el servidor")
                    else:
                        if respuesta.status_code == 200:
                            st.success("Precio actualizado correctamente")
                            st.rerun()
                        else:
                            st.error("Error al modificar el precio")

                if cancha["activa"]:
                    if st.button(
                        "Dar de baja cancha",
                        key=f"eliminar_{cancha['id']}"
                    ):
                        try:
                            respuesta = eliminar_cancha(cancha["id"])
                        except requests.exceptions.RequestException:
                            st.error("No se pudo conectar con el servidor")
                        else:
                            if respuesta.status_code == 200:
                                st.success("Cancha dada de baja")
                                st.rerun()
                            else:
                                st.error("Error al eliminar cancha")

            if usuario["rol"] == "COMUN":

                st.write("### Reservar cancha")

                fecha = st.date_input(
                    "Fecha",
                    value=date.today(),
                    key=f"fecha_{cancha['id']}"
                )

                hora_inicio = st.selectbox(
                    "Hora de inicio",
                    HORARIOS,
                    key=f"hora_inicio_{cancha['id']}"
                )

                hora_fin = st.selectbox(
                    "Hora de fin",
                    HORARIOS,
                    key=f"hora_fin_{cancha['id']}"
                )

                if st.button(
                    "Continuar al pago",
                    key=f"reservar_{cancha['id']}"
                ):
                    try:
                        respuesta = realizar_reserva(
                            usuario["id"],
                            cancha["id"],
                            fecha,
                            hora_inicio,
                            hora_fin
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