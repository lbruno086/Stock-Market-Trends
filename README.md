# Stock Market Trends
 Guide to create candlestick charts with moving averages and volume. The contents of this script can be found described in detailed here: https://medium.com/i-want-to-be-the-very-best/stock-market-trends-b24203484e0f

## AI agents (TradingAgents + DeepSeek V4 Pro)
`ai_agents/run_tradingagents.py` runs [TradingAgents](https://github.com/TauricResearch/TradingAgents), a multi-agent LLM framework (analysts, bull/bear debate, trader, risk team, portfolio manager), using DeepSeek `deepseek-v4-pro`.

```bash
pip install -r ai_agents/requirements.txt     # Python 3.11+
cp ai_agents/.env.example .env                 # put your DEEPSEEK_API_KEY there
python ai_agents/run_tradingagents.py          # asks for a ticker, prints the report and the suggestion
python ai_agents/run_tradingagents.py NVDA     # or pass the ticker directly
```
Reports are also saved (with a single-page HTML) under `~/.tradingagents`.
Research tool only — not financial advice.
