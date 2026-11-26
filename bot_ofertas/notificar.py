"""Envío de avisos por Telegram y/o email (SMTP). Se configuran con variables de entorno."""
from __future__ import annotations

import json
import logging
import os
import smtplib
import urllib.request
from email.mime.text import MIMEText

log = logging.getLogger("notificar")


def _fmt(n: float) -> str:
    return f"${n:,.0f}".replace(",", ".")


def formatear(ofertas) -> str:
    lineas = [f"🏷️ {len(ofertas)} oferta(s) con gran descuento\n"]
    for o in sorted(ofertas, key=lambda x: -x.descuento):
        ico = "🏨" if o.tipo.startswith("hotel") else "🏡"
        precio = _fmt(o.precio)
        if o.precio_original:
            precio = f"{precio} (antes {_fmt(o.precio_original)})"
        motivo = []
        if o.descuento_publicado:
            motivo.append(f"-{o.descuento_publicado:.0f}% publicado")
        if o.descuento_historial:
            motivo.append(f"-{o.descuento_historial:.0f}% vs. historial")
        lineas.append(
            f"{ico} {o.nombre} ({o.tipo}, {o.zona})\n"
            f"   {o.checkin} → {o.checkout} · {precio} · {' / '.join(motivo)}"
            + (f" · ⭐ {o.puntaje}" if o.puntaje else "")
            + f"\n   {o.url.split('?')[0]}\n"
        )
    return "\n".join(lineas)


def telegram(texto: str) -> bool:
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    for i in range(0, len(texto), 3900):  # límite de Telegram: 4096 caracteres
        data = json.dumps({"chat_id": chat, "text": texto[i:i + 3900],
                           "disable_web_page_preview": True}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage",
                                     data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20).read()
    return True


def email(texto: str) -> bool:
    user, pwd, to = os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"), os.getenv("EMAIL_TO")
    if not user or not pwd or not to:
        return False
    msg = MIMEText(texto, "plain", "utf-8")
    msg["Subject"] = "Ofertas: quintas y hoteles 4★ (Pilar / Luján / Escobar)"
    msg["From"], msg["To"] = user, to
    with smtplib.SMTP_SSL(os.getenv("SMTP_HOST", "smtp.gmail.com"), 465, timeout=30) as s:
        s.login(user, pwd)
        s.send_message(msg)
    return True


def enviar(ofertas):
    if not ofertas:
        return
    texto = formatear(ofertas)
    print(texto)
    for canal in (telegram, email):
        try:
            if canal(texto):
                log.info("Aviso enviado por %s", canal.__name__)
        except Exception as e:
            log.error("Falló %s: %s", canal.__name__, e)
