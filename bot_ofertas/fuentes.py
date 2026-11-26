"""Scrapers con Playwright: Booking (hoteles 4★) y Airbnb (quintas)."""
from __future__ import annotations

import logging
import urllib.parse as up
from dataclasses import dataclass

from precios import parsear_precio

log = logging.getLogger("fuentes")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class Oferta:
    fuente: str
    tipo: str          # "hotel 4★" | "quinta"
    zona: str
    nombre: str
    url: str
    checkin: str
    checkout: str
    precio: float
    precio_original: float | None = None
    descuento_publicado: float = 0.0
    descuento_historial: float = 0.0
    puntaje: str = ""

    @property
    def clave(self) -> str:
        base = self.url.split("?")[0]
        return f"{self.fuente}|{base}|{self.checkin}"

    @property
    def descuento(self) -> float:
        return max(self.descuento_publicado, self.descuento_historial)


# JS que corre en la página: por cada tarjeta, devuelve nombre, link, textos
# de precios tachados (line-through) y precio actual.
_JS_TARJETAS = r"""
(cfg) => {
  const out = [];
  for (const card of document.querySelectorAll(cfg.card)) {
    const t = card.querySelector(cfg.title);
    const a = card.querySelector(cfg.link) || card.querySelector('a[href]');
    const tachados = [];
    for (const el of card.querySelectorAll('span, div, s, del')) {
      if (el.children.length > 2) continue;
      const st = getComputedStyle(el);
      if ((st.textDecorationLine || '').includes('line-through') || el.tagName === 'DEL' || el.tagName === 'S') {
        const tx = el.innerText.trim();
        if (/\d/.test(tx)) tachados.push(tx);
      }
    }
    const pEl = cfg.price ? card.querySelector(cfg.price) : null;
    const score = cfg.score ? card.querySelector(cfg.score) : null;
    out.push({
      nombre: t ? t.innerText.trim() : '',
      url: a ? a.href : '',
      tachados,
      precio: pEl ? pEl.innerText.trim() : '',
      texto: card.innerText,
      puntaje: score ? ((score.innerText.match(/\d{1,2}[,.]\d/) || [''])[0]) : ''
    });
  }
  return out;
}
"""


def _precio_actual(precio_txt: str, texto: str, tachados: list[str]) -> float | None:
    """El precio actual es el primer monto que no está tachado."""
    import re
    vistos = {parsear_precio(x) for x in tachados}
    for monto in re.findall(r"(?:US\$|ARS|\$)\s*\d[\d.,]*", precio_txt or texto):
        p = parsear_precio(monto)
        if p and p not in vistos and p > 1000:
            return p
    return None


def _a_ofertas(filas, fuente, tipo, zona, checkin, checkout) -> list[Oferta]:
    res = []
    for f in filas:
        if not f["nombre"] or not f["url"]:
            continue
        actual = _precio_actual(f["precio"], f["texto"], f["tachados"])
        if not actual:
            continue
        originales = [p for p in (parsear_precio(x) for x in f["tachados"]) if p and p > actual]
        original = max(originales) if originales else None
        from precios import descuento_pct
        res.append(Oferta(
            fuente=fuente, tipo=tipo, zona=zona, nombre=f["nombre"], url=f["url"],
            checkin=checkin, checkout=checkout, precio=actual, precio_original=original,
            descuento_publicado=descuento_pct(original, actual), puntaje=f.get("puntaje", ""),
        ))
    return res


def url_booking(destino, checkin, checkout, huespedes, moneda):
    q = {
        "ss": destino, "checkin": checkin, "checkout": checkout,
        "group_adults": huespedes, "no_rooms": 1, "group_children": 0,
        "nflt": "class=4", "selected_currency": moneda, "order": "price",
    }
    return "https://www.booking.com/searchresults.es-ar.html?" + up.urlencode(q)


def url_airbnb(destino, checkin, checkout, huespedes, moneda, pileta, min_dorm):
    slug = up.quote(destino.replace(", ", "--").replace(" ", "-"))
    q = [
        ("checkin", checkin), ("checkout", checkout), ("adults", huespedes),
        ("currency", moneda), ("room_types[]", "Entire home/apt"),
        ("min_bedrooms", min_dorm), ("query", destino),
    ]
    if pileta:
        q.append(("amenities[]", 7))  # 7 = pileta en Airbnb
    return f"https://www.airbnb.com.ar/s/{slug}/homes?" + up.urlencode(q)


def _cargar(page, url, card_sel, scrolls=4):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    for sel in ("#onetrust-accept-btn-handler", 'button:has-text("Aceptar")',
                'button[aria-label="Descartar información sobre el inicio de sesión."]'):
        try:
            page.click(sel, timeout=2500)
        except Exception:
            pass
    try:
        page.wait_for_selector(card_sel, timeout=30000)
    except Exception:
        log.warning("No aparecieron resultados en %s", url)
        return False
    for _ in range(scrolls):
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(1200)
    return True


def buscar_booking(page, zona, checkin, checkout, cfg) -> list[Oferta]:
    url = url_booking(zona["busqueda"], checkin, checkout, cfg["huespedes"], cfg["moneda"])
    if not _cargar(page, url, '[data-testid="property-card"]'):
        return []
    filas = page.evaluate(_JS_TARJETAS, {
        "card": '[data-testid="property-card"]', "title": '[data-testid="title"]',
        "link": 'a[data-testid="title-link"]',
        "price": '[data-testid="price-and-discounted-price"]',
        "score": '[data-testid="review-score"]',
    })
    # Booking muestra el tachado y el actual en el mismo bloque
    for f in filas:
        f["precio"] = ""  # usar el texto completo y descartar tachados
    return _a_ofertas(filas, "Booking", "hotel 4★", zona["nombre"], checkin, checkout)


def buscar_airbnb(page, zona, checkin, checkout, cfg) -> list[Oferta]:
    q = cfg.get("quintas", {})
    url = url_airbnb(zona["busqueda"], checkin, checkout, cfg["huespedes"], cfg["moneda"],
                     q.get("solo_con_pileta", True), q.get("min_dormitorios", 1))
    if not _cargar(page, url, '[data-testid="card-container"]', scrolls=2):
        return []
    filas = page.evaluate(_JS_TARJETAS, {
        "card": '[data-testid="card-container"]', "title": '[data-testid="listing-card-title"]',
        "link": "a[href*='/rooms/']", "price": "", "score": "",
    })
    for f in filas:
        sub = f["texto"].splitlines()
        # Título más descriptivo: tipo + subtítulo
        if len(sub) > 1 and f["nombre"]:
            f["nombre"] = f["nombre"] + " — " + sub[1] if sub[1] != f["nombre"] else f["nombre"]
    return _a_ofertas(filas, "Airbnb", "quinta", zona["nombre"], checkin, checkout)
