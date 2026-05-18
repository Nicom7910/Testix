import json
import os


def leer_archivo(ruta):
    if not os.path.exists(ruta):
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump([], archivo)

    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_archivo(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)


def obtener_siguiente_id(datos):
    if len(datos) == 0:
        return 1

    mayor_id = max(item["id"] for item in datos)
    return mayor_id + 1