"""Bot de ofertas: quintas y hoteles 4★ en Pilar, Luján y Escobar.

Uso:
    python bot.py            # una pasada (ideal para GitHub Actions / cron)
    python bot.py --loop     # corre para siempre, una pasada por hora
"""
from __future__ import annotations

import argparse
import logging
import os
import random
import sys
import time
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
import fuentes  # noqa: E402
import notificar  # noqa: E402
from almacen import Almacen  # noqa: E402
from precios import descuento_vs_historial, proximos_fines_de_semana  # noqa: E402

AQUI = Path(__file__).parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bot")


def una_pasada(cfg: dict, almacen: Almacen) -> list:
    buscadores = []
    if cfg["fuentes"].get("booking_hoteles_4_estrellas"):
        buscadores.append(fuentes.buscar_booking)
    if cfg["fuentes"].get("airbnb_quintas"):
        buscadores.append(fuentes.buscar_airbnb)

    fechas = proximos_fines_de_semana(cfg["fines_de_semana"], cfg["noches"])
    encontradas = []
    with sync_playwright() as p:
        nav = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = nav.new_context(user_agent=fuentes.UA, locale="es-AR",
                              timezone_id="America/Argentina/Buenos_Aires",
                              viewport={"width": 1366, "height": 900})
        page = ctx.new_page()
        for zona in cfg["zonas"]:
            for ci, co in fechas:
                for buscar in buscadores:
                    try:
                        res = buscar(page, zona, ci.isoformat(), co.isoformat(), cfg)
                        log.info("%s %s %s: %d resultados", buscar.__name__, zona["nombre"], ci, len(res))
                        encontradas += res
                    except Exception as e:
                        log.error("%s %s falló: %s", buscar.__name__, zona["nombre"], e)
                    time.sleep(random.uniform(3, 7))  # ser amable con los sitios
        nav.close()

    ofertas = []
    for o in encontradas:
        o.descuento_historial = descuento_vs_historial(
            almacen.historial(o.clave), o.precio, cfg["min_observaciones_historial"])
        almacen.registrar(o.clave, o.precio)
        if o.descuento >= cfg["descuento_minimo"] and not almacen.ya_avisado(o.clave, o.precio):
            ofertas.append(o)
            almacen.marcar_avisado(o.clave, o.precio, o.descuento)
    almacen.guardar()
    log.info("Total: %d resultados, %d ofertas nuevas >= %s%%",
             len(encontradas), len(ofertas), cfg["descuento_minimo"])
    notificar.enviar(ofertas)
    return ofertas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true", help="repetir cada intervalo (1 h por defecto)")
    ap.add_argument("--config", default=str(AQUI / "config.yaml"))
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    almacen = Almacen(os.getenv("BOT_DB", str(AQUI / "estado.sqlite")))
    while True:
        try:
            una_pasada(cfg, almacen)
        except Exception:
            log.exception("Error en la pasada")
        if not args.loop:
            break
        log.info("Durmiendo %s s…", cfg["intervalo_segundos"])
        time.sleep(cfg["intervalo_segundos"])


if __name__ == "__main__":
    main()
