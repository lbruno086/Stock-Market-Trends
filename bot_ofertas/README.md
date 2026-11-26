# Bot de ofertas: quintas y hoteles 4★ (Pilar, Luján, Escobar)

Cada hora busca:
- **Hoteles 4 estrellas** en [Booking.com](https://www.booking.com) (filtro de 4★, ordenados por precio)
- **Quintas** (casa entera, con pileta, 2+ dormitorios) en [Airbnb](https://www.airbnb.com.ar)

para los próximos fines de semana (viernes a domingo) en Pilar, Luján y Escobar, y **te avisa por Telegram y/o email** cuando encuentra un descuento de **30 % o más**, contando como descuento:
1. **Descuento publicado**: el sitio muestra el precio tachado.
2. **Descuento contra el historial**: el precio está ≥30 % por debajo de la mediana de lo que el bot vio antes para ese mismo lugar y fecha.

No repite avisos: solo vuelve a avisar si esa misma oferta baja todavía más.

## Ponerlo en marcha (GitHub Actions, gratis)

1. **Telegram**: hablá con [@BotFather](https://t.me/BotFather) → `/newbot` → copiá el token. Mandale un mensaje a tu bot y buscá tu `chat_id` en `https://api.telegram.org/bot<TOKEN>/getUpdates`.
2. En el repo: **Settings → Secrets and variables → Actions → New repository secret** y cargá:
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - (opcional, email) `SMTP_USER` (tu Gmail), `SMTP_PASSWORD` ([contraseña de aplicación de Google](https://myaccount.google.com/apppasswords)), `EMAIL_TO`
3. Mergeá esta rama a la rama principal (GitHub solo ejecuta los cron desde la rama por defecto).
4. **Actions → "Bot ofertas quintas y hoteles" → Run workflow** para probarlo al instante. Después corre solo cada hora.

## Correrlo en tu compu

```bash
cd bot_ofertas
pip install -r requirements.txt
python -m playwright install chromium
export TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=...
python bot.py --loop      # una pasada por hora, sin parar
```

## Ajustes (`config.yaml`)

| Opción | Qué hace |
|---|---|
| `zonas` | Localidades a buscar |
| `fines_de_semana`, `noches`, `huespedes` | Fechas y ocupación |
| `descuento_minimo` | % mínimo para avisar (30 por defecto) |
| `quintas.solo_con_pileta`, `quintas.min_dormitorios` | Filtros de quintas |
| `fuentes` | Activar/desactivar Booking o Airbnb |

## Pruebas

```bash
pip install pytest && python -m pytest -q tests
```

> Nota: los sitios cambian su HTML de vez en cuando; si una fuente deja de traer resultados, el log de Actions lo muestra ("No aparecieron resultados") y hay que ajustar los selectores en `fuentes.py`.
