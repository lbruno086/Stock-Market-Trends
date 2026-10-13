# Stock Market Trends
 Guide to create candlestick charts with moving averages and volume. The contents of this script can be found described in detailed here: https://medium.com/i-want-to-be-the-very-best/stock-market-trends-b24203484e0f

## AI agents (TradingAgents + DeepSeek V4 Pro)
`ai_agents/run_tradingagents.py` runs [TradingAgents](https://github.com/TauricResearch/TradingAgents), a multi-agent LLM framework (analysts, bull/bear debate, trader, risk team, portfolio manager), using DeepSeek `deepseek-v4-pro`.

```bash
pip install -r ai_agents/requirements.txt     # Python 3.11+
export DEEPSEEK_API_KEY=...                    # or put it in .env
python ai_agents/run_tradingagents.py NVDA 2026-10-10
```
Research tool only — not financial advice.
