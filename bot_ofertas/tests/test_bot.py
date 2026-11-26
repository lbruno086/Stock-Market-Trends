"""Pruebas offline: parseo de precios y extracción desde HTML de ejemplo."""
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import fuentes  # noqa: E402
from almacen import Almacen  # noqa: E402
from precios import (descuento_pct, descuento_vs_historial, parsear_precio,  # noqa: E402
                     proximos_fines_de_semana)

BOOKING = """
<div data-testid="property-card"><a data-testid="title-link" href="https://www.booking.com/hotel/ar/howard-johnson-pilar.html?x=1">
<div data-testid="title">Hotel Pilar Plaza</div></a>
<div data-testid="review-score">8,7\nMuy bien</div>
<div data-testid="price-and-discounted-price"><span style="text-decoration:line-through">ARS 300.000</span> <span>ARS 180.000</span></div>
<div>Incluye impuestos</div></div>
<div data-testid="property-card"><a data-testid="title-link" href="https://www.booking.com/hotel/ar/escobar.html">
<div data-testid="title">Escobar Suites</div></a>
<div data-testid="price-and-discounted-price"><span>ARS 210.000</span></div></div>
"""
AIRBNB = """
<div data-testid="card-container"><a href="https://www.airbnb.com.ar/rooms/123?c=1">
<div data-testid="listing-card-title">Casa de campo en Luján</div><div>Quinta con pileta y parrilla</div>
<span><del>$ 500.000</del> $ 250.000 por 2 noches</span></a></div>
"""


def test_parsear_precio():
    assert parsear_precio("ARS 185.000") == 185000
    assert parsear_precio("$ 1.234.567,50") == 1234567.5
    assert parsear_precio("US$1,200.00") == 1200
    assert parsear_precio("sin precio") is None


def test_descuentos():
    assert descuento_pct(300000, 180000) == 40.0
    assert descuento_vs_historial([100, 100, 100], 60, 3) == 40.0
    assert descuento_vs_historial([100], 60, 3) == 0.0


def test_fines_de_semana():
    fechas = proximos_fines_de_semana(2, 2, hoy=dt.date(2026, 11, 26))
    assert fechas[0] == (dt.date(2026, 11, 27), dt.date(2026, 11, 29))
    assert fechas[1][0] == dt.date(2026, 12, 4)


def _page(html):
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    exe = os.getenv("CHROMIUM_PATH")
    nav = pw.chromium.launch(**({"executable_path": exe} if exe else {}))
    page = nav.new_page()
    page.set_content(html)
    return pw, nav, page


def test_scrapers(monkeypatch):
    monkeypatch.setattr(fuentes, "_cargar", lambda *a, **k: True)
    cfg = {"huespedes": 2, "moneda": "ARS", "quintas": {}}
    pw, nav, page = _page(BOOKING)
    try:
        r = fuentes.buscar_booking(page, {"nombre": "Pilar", "busqueda": "Pilar"}, "2026-11-27", "2026-11-29", cfg)
        assert [(o.nombre, o.precio, o.descuento_publicado) for o in r] == [
            ("Hotel Pilar Plaza", 180000, 40.0), ("Escobar Suites", 210000, 0.0)]
        assert r[0].puntaje == "8,7"
        page.set_content(AIRBNB)
        r = fuentes.buscar_airbnb(page, {"nombre": "Luján", "busqueda": "Luján"}, "2026-11-27", "2026-11-29", cfg)
        assert len(r) == 1 and r[0].precio == 250000 and r[0].descuento_publicado == 50.0
        assert "pileta" in r[0].nombre
    finally:
        nav.close(); pw.stop()


def test_almacen(tmp_path):
    a = Almacen(str(tmp_path / "e.sqlite"))
    a.registrar("k", 100); a.marcar_avisado("k", 100, 40)
    assert a.historial("k") == [100]
    assert a.ya_avisado("k", 100) and not a.ya_avisado("k", 90)
