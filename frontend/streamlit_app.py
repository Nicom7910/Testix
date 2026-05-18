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


def login(email, password):
    return requests.post(
        f"{API_URL}/usuarios/login",
        json={
            "email": email,
            "password": password
        },
        timeout=5
    )


def obtener_canchas():
    respuesta = requests.get(
        f"{API_URL}/canchas/disponibles",
        timeout=5
    )
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
    return requests.delete(
        f"{API_URL}/canchas/{cancha_id}",
        timeout=5
    )


def realizar_reserva(usuario_id, cancha_id, fecha, hora):
    return requests.post(
        f"{API_URL}/reservas/",
        json={
            "usuario_id": usuario_id,
            "cancha_id": cancha_id,
            "fecha": str(fecha),
            "hora": hora
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


def cancelar_reserva(reserva_id):
    return requests.delete(
        f"{API_URL}/reservas/{reserva_id}",
        timeout=5
    )


# LOGIN
if st.session_state.usuario is None:

    st.title("🎾 Reserva de Canchas")
    st.subheader("Iniciar sesión")

    email = st.text_input("Email")
    password = st.text_input("Contraseña", type="password")

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


# PANTALLA PRINCIPAL
else:

    usuario = st.session_state.usuario

    st.title("🎾 Sistema de Reservas")

    st.success(
        f"Bienvenido {usuario['nombre']} - Rol: {usuario['rol']}"
    )

    if st.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.rerun()

    st.divider()

    # PANEL ADMINISTRADOR
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
            min_value=1
        )

        if st.button("Crear cancha"):
            if nombre == "":
                st.warning("Debe ingresar el nombre de la cancha")
            else:
                try:
                    respuesta = crear_cancha(
                        nombre,
                        superficie,
                        techada,
                        precio
                    )
                except requests.exceptions.RequestException:
                    st.error("No se pudo conectar con el servidor")
                else:
                    if respuesta.status_code == 200:
                        st.success("Cancha creada correctamente")
                        st.rerun()
                    else:
                        st.error("Error al crear la cancha")

        st.divider()

    # RESERVAS ACTIVAS DEL USUARIO COMUN
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
                    st.write(f"Hora: {reserva['hora']}")
                    st.write(f"Monto total: ${reserva['monto_total']}")
                    st.write(f"Seña pagada 50%: ${reserva['sena']}")

                    if st.button(
                        "Cancelar reserva",
                        key=f"cancelar_{reserva['id']}"
                    ):
                        try:
                            respuesta = cancelar_reserva(reserva["id"])
                        except requests.exceptions.RequestException:
                            st.error("No se pudo conectar con el servidor")
                        else:
                            if respuesta.status_code == 200:
                                st.success("Reserva cancelada correctamente")
                                st.rerun()
                            else:
                                st.error("Error al cancelar la reserva")

        st.divider()

    # LISTADO DE CANCHAS
    st.header("Canchas disponibles")

    try:
        canchas = obtener_canchas()
    except requests.exceptions.RequestException:
        st.error("No se pudo conectar con el servidor")
        canchas = []

    if len(canchas) == 0:
        st.warning("No hay canchas disponibles")

    for cancha in canchas:

        with st.container(border=True):

            st.subheader(cancha["nombre"])

            st.write(f"Superficie: {cancha['tipo_superficie']}")
            st.write(f"Techada: {'Sí' if cancha['techada'] else 'No'}")
            st.write(f"Precio por hora: ${cancha['precio_por_hora']}")

            # USUARIO COMUN
            if usuario["rol"] == "COMUN":

                st.write("### Reservar cancha")

                fecha = st.date_input(
                    "Fecha",
                    value=date.today(),
                    key=f"fecha_{cancha['id']}"
                )

                hora = st.selectbox(
                    "Hora",
                    [
                        "08:00",
                        "09:00",
                        "10:00",
                        "11:00",
                        "12:00",
                        "13:00",
                        "14:00",
                        "15:00",
                        "16:00",
                        "17:00",
                        "18:00",
                        "19:00",
                        "20:00",
                        "21:00",
                        "22:00"
                    ],
                    key=f"hora_{cancha['id']}"
                )

                if st.button(
                    "Reservar",
                    key=f"reservar_{cancha['id']}"
                ):
                    try:
                        respuesta = realizar_reserva(
                            usuario["id"],
                            cancha["id"],
                            fecha,
                            hora
                        )
                    except requests.exceptions.RequestException:
                        st.error("No se pudo conectar con el servidor")
                    else:
                        if respuesta.status_code == 200:
                            datos = respuesta.json()

                            st.success("Reserva realizada correctamente")
                            st.info(
                                f"Seña requerida: ${datos['sena']} "
                                f"(50% del valor total de ${datos['monto_total']})"
                            )

                            st.rerun()
                        else:
                            try:
                                st.error(respuesta.json()["detail"])
                            except:
                                st.error("Error al realizar la reserva")

            # ADMINISTRADOR
            if usuario["rol"] == "ADMINISTRADOR":

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