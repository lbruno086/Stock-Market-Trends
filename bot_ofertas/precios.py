"""Utilidades puras: parseo de precios, fechas y cálculo de descuentos."""
from __future__ import annotations

import datetime as dt
import re
import statistics

_NUM = re.compile(r"\d[\d.,\s]*\d|\d")


def parsear_precio(texto: str | None) -> float | None:
    """'ARS 185.000' -> 185000.0 ; '$ 1.234.567,50' -> 1234567.5 ; 'US$1,200' -> 1200."""
    if not texto:
        return None
    m = _NUM.search(texto.replace("\xa0", " "))
    if not m:
        return None
    s = m.group(0).replace(" ", "")
    # Decimal con coma (formato AR): termina en ,dd
    if re.search(r",\d{1,2}$", s):
        s = s.replace(".", "").replace(",", ".")
    # Decimal con punto (formato US): termina en .dd y hay comas de miles o un solo punto
    elif re.search(r"\.\d{1,2}$", s) and s.count(".") == 1 and "," in s:
        s = s.replace(",", "")
    else:
        s = s.replace(".", "").replace(",", "")
    try:
        valor = float(s)
    except ValueError:
        return None
    return valor if valor > 0 else None


def descuento_pct(original: float | None, actual: float | None) -> float:
    if not original or not actual or actual >= original:
        return 0.0
    return round((1 - actual / original) * 100, 1)


def descuento_vs_historial(historial: list[float], actual: float, minimo: int) -> float:
    if len(historial) < minimo:
        return 0.0
    return descuento_pct(statistics.median(historial), actual)


def proximos_fines_de_semana(cantidad: int, noches: int, hoy: dt.date | None = None):
    """Devuelve [(checkin, checkout), ...] empezando el próximo viernes."""
    hoy = hoy or dt.date.today()
    dias = (4 - hoy.weekday()) % 7  # 4 = viernes
    if dias == 0:
        dias = 7 if dt.datetime.now().hour >= 12 else 0
    viernes = hoy + dt.timedelta(days=dias)
    return [
        (viernes + dt.timedelta(weeks=i), viernes + dt.timedelta(weeks=i, days=noches))
        for i in range(cantidad)
    ]
