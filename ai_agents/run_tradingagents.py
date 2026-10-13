"""Asesor de acciones con IA: TradingAgents + DeepSeek V4 Pro.

Al abrirlo pide un ticker, corre el equipo de agentes (analistas, debate
alcista/bajista, trader, riesgo y portfolio manager) y muestra el informe
con la sugerencia final (COMPRAR / MANTENER / VENDER).

Uso:
    python ai_agents/run_tradingagents.py            # modo interactivo
    python ai_agents/run_tradingagents.py NVDA       # directo con un ticker
    python ai_agents/run_tradingagents.py NVDA 2026-10-10

Requiere DEEPSEEK_API_KEY (variable de entorno o archivo .env).
"""
import argparse
import datetime
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
from tradingagents.graph.trading_graph import TradingAgentsGraph  # noqa: E402

MODEL = "deepseek-v4-pro"

SECTIONS = [
    ("market_report", "📈 Análisis técnico"),
    ("sentiment_report", "💬 Sentimiento (redes sociales)"),
    ("news_report", "📰 Noticias y macro"),
    ("fundamentals_report", "🏦 Fundamentales"),
    ("investment_plan", "⚖️  Debate alcista vs bajista (Research Manager)"),
    ("trader_investment_plan", "💼 Propuesta del trader"),
    ("final_trade_decision", "✅ Decisión final (Portfolio Manager)"),
]


def last_weekday(today=None):
    day = (today or datetime.date.today()) - datetime.timedelta(days=1)
    while day.weekday() >= 5:
        day -= datetime.timedelta(days=1)
    return day.isoformat()


def build_graph(analysts, debate_rounds, language):
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "deepseek"
    config["deep_think_llm"] = MODEL
    config["quick_think_llm"] = MODEL
    config["max_debate_rounds"] = debate_rounds
    config["max_risk_discuss_rounds"] = debate_rounds
    config["output_language"] = language
    return TradingAgentsGraph(selected_analysts=analysts, debug=False, config=config)


def print_report(ticker, date, state, decision, report_dir):
    line = "=" * 70
    print(f"\n{line}\n INFORME {ticker} — {date}\n{line}")
    for key, title in SECTIONS:
        text = (state.get(key) or "").strip()
        if text:
            print(f"\n{title}\n{'-' * 70}\n{text}\n")
    print(line)
    print(f" 🎯 SUGERENCIA PARA {ticker}: {decision}")
    print(line)
    print(f" Informe completo guardado en: {report_dir}")
    print(" Herramienta de investigación — no es consejo financiero.\n")


def analyze(graph, ticker, date):
    ticker = ticker.strip().upper()
    print(f"\nAnalizando {ticker} al {date} con {MODEL}... (puede tardar unos minutos)")
    state, decision = graph.propagate(ticker, date)
    report_dir = graph.save_reports(state, ticker)
    print_report(ticker, date, state, decision, report_dir)


def main():
    parser = argparse.ArgumentParser(description="Asesor de acciones con TradingAgents + DeepSeek V4 Pro")
    parser.add_argument("ticker", nargs="?", help="Ticker, p. ej. NVDA (si se omite, se pregunta)")
    parser.add_argument("date", nargs="?", default=None, help="Fecha YYYY-MM-DD (por defecto, último día hábil)")
    parser.add_argument("--analysts", default="market,social,news,fundamentals",
                        help="Analistas separados por coma")
    parser.add_argument("--debate-rounds", type=int, default=1)
    parser.add_argument("--language", default="Spanish", help="Idioma de los informes")
    args = parser.parse_args()

    if not os.environ.get("DEEPSEEK_API_KEY"):
        sys.exit("Falta DEEPSEEK_API_KEY. Agrégala como variable de entorno o en un archivo .env.")

    graph = build_graph(args.analysts.split(","), args.debate_rounds, args.language)

    if args.ticker:
        analyze(graph, args.ticker, args.date or last_weekday())
        return

    print(f"Asesor de acciones con IA ({MODEL}). Enter vacío o 'salir' para terminar.")
    while True:
        try:
            ticker = input("\nTicker: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not ticker or ticker.lower() in ("salir", "exit", "q"):
            break
        default_date = last_weekday()
        date = input(f"Fecha [{default_date}]: ").strip() or default_date
        try:
            analyze(graph, ticker, date)
        except Exception as exc:  # keep the session alive on a bad ticker or API error
            print(f"Error analizando {ticker.upper()}: {exc}")


if __name__ == "__main__":
    main()
