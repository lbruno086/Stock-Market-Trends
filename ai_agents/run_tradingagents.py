"""Run TradingAgents (multi-agent LLM trading analysis) using DeepSeek V4 Pro.

Usage:
    python ai_agents/run_tradingagents.py NVDA 2026-10-10
    python ai_agents/run_tradingagents.py AAPL            # date defaults to the last weekday

Requires the DEEPSEEK_API_KEY environment variable (see ai_agents/.env.example).
"""
import argparse
import datetime
import os
import sys

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

MODEL = "deepseek-v4-pro"


def last_weekday(today=None):
    day = (today or datetime.date.today()) - datetime.timedelta(days=1)
    while day.weekday() >= 5:
        day -= datetime.timedelta(days=1)
    return day.isoformat()


def main():
    parser = argparse.ArgumentParser(description="TradingAgents with DeepSeek V4 Pro")
    parser.add_argument("ticker", help="Stock ticker, e.g. NVDA")
    parser.add_argument("date", nargs="?", default=last_weekday(), help="Trade date YYYY-MM-DD")
    parser.add_argument("--analysts", default="market,social,news,fundamentals",
                        help="Comma-separated analysts to run")
    parser.add_argument("--debate-rounds", type=int, default=1)
    parser.add_argument("--language", default="Spanish", help="Language of the reports")
    args = parser.parse_args()

    if not os.environ.get("DEEPSEEK_API_KEY"):
        sys.exit("DEEPSEEK_API_KEY is not set. Add it to your environment or .env file.")

    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "deepseek"
    config["deep_think_llm"] = MODEL
    config["quick_think_llm"] = MODEL
    config["max_debate_rounds"] = args.debate_rounds
    config["max_risk_discuss_rounds"] = args.debate_rounds
    config["output_language"] = args.language

    graph = TradingAgentsGraph(
        selected_analysts=args.analysts.split(","), debug=True, config=config
    )
    state, decision = graph.propagate(args.ticker.upper(), args.date)
    graph.save_reports(state, args.ticker.upper())

    print("\n" + "=" * 60)
    print(f"{args.ticker.upper()} @ {args.date} -> {decision}")


if __name__ == "__main__":
    main()
