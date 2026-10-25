"""
Foto del estado en tiempo real de las estaciones de recarga de España en Electromaps.

El listado por zonas (/mapi/v2/locations con realtime=true) devuelve solo las estaciones
cuyos conectores informan su estado en tiempo real, con un campo `marker` = "potencia.estado.3":

    potencia  0 = hasta ~7,4 kW | 1 = 11-30 kW (AC) | 2 = 50-105 kW | 3 = >= 150 kW
    estado    0 = algun conector libre
              1 = todos fuera de servicio
              2 = ninguno libre y alguno ocupado
              3 = desconocido

Una foto de toda España son ~150 peticiones ligeras, en serie, con pausa y reintentos.

Salida: <dir>/AAAA-MM-DDTHHMMSSZ.csv.gz, una fila por estacion:
    instante_utc, site_id, potencia, estado

Uso:
    python3 estado.py --dir estado
"""

import argparse
import csv
import gzip
import os
import random
import sys
import time
from datetime import datetime, timezone

import requests

URL = "https://www.electromaps.com/mapi/v2/locations"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.electromaps.com/",
    "Origin": "https://www.electromaps.com",
}
PAUSA_S = (0.3, 0.8)
REINTENTOS = 5
# (norte, sur, este, oeste): peninsula y Baleares, Canarias
ZONAS = [(43.8, 35.2, 4.6, -9.5), (29.5, 27.5, -13.0, -18.5)]
PASO = 1.0


def cuadriculas():
    for norte, sur, este, oeste in ZONAS:
        lat = sur
        while lat < norte:
            lng = oeste
            while lng < este:
                yield min(lat + PASO, norte), min(lng + PASO, este), lat, lng
                lng += PASO
            lat += PASO


def get(params):
    for intento in range(REINTENTOS):
        try:
            r = requests.get(URL, params=params, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        time.sleep(2 ** intento + random.random())
    return None


def foto():
    instante = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    filas, vistos, fallos = [], set(), 0
    for lat_ne, lng_ne, lat_sw, lng_sw in cuadriculas():
        datos = get(dict(latNE=lat_ne, lngNE=lng_ne, latSW=lat_sw, lngSW=lng_sw,
                         realtime="true", skipAuthTokenValidation="true"))
        if datos is None:
            fallos += 1
            continue
        for x in datos:
            if x["id"] in vistos:
                continue
            vistos.add(x["id"])
            partes = (x.get("marker") or "").split(".")
            if len(partes) == 3:
                filas.append((instante, x["id"], partes[0], partes[1]))
        time.sleep(random.uniform(*PAUSA_S))
    return instante, filas, fallos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="estado", help="carpeta de salida")
    args = ap.parse_args()
    t0 = time.time()
    instante, filas, fallos = foto()
    if not filas:
        print(f"{instante}  sin datos ({fallos} cuadriculas fallidas)", flush=True)
        sys.exit(1)
    os.makedirs(args.dir, exist_ok=True)
    ruta = os.path.join(args.dir, instante.replace(":", "") + ".csv.gz")
    with gzip.open(ruta, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["instante_utc", "site_id", "potencia", "estado"])
        w.writerows(filas)
    print(f"{instante}  {len(filas)} estaciones ({time.time() - t0:.0f} s, {fallos} cuadriculas fallidas) -> {ruta}",
          flush=True)


if __name__ == "__main__":
    main()
