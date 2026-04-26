# ⚡ AI 量化分析 API

> FastAPI 多 Agent 量化分析後端（純 API，無前端）。
> 支援美股、台股、台股 ETF、加密貨幣（皆透過 yfinance）。

---

## 🚀 快速啟動

```bash
pip install -r requirements.txt
cp .env.example .env          # 填 API Keys（純跑 keyword 模式可不填）
uvicorn app.main:app --reload
```

互動式 API 文件：http://localhost:8000/docs

跑測試：

```bash
pytest                         # 全部 (59 個測試，不依賴外網)
pytest tests/test_indicator_engine.py -v
```

---

## 📁 專案結構

```
ai-quant-starter2/
├── requirements.txt
├── .env.example
├── Dockerfile
├── CLAUDE.md                   # 給 Claude Code 的專案指引
├── app/
│   ├── main.py                 # FastAPI endpoints
│   ├── config.py               # 環境變數
│   ├── orchestrator.py         # 流程協調
│   ├── agents/
│   │   ├── technical_agent.py  # 9 指標規則表評分
│   │   ├── news_agent.py       # keyword / gemini / claude 三模式
│   │   ├── risk_agent.py       # 風險等級判定
│   │   └── decision_agent.py   # 加權合成 → 訊號 + 交易計畫
│   └── services/
│       ├── market_data.py      # symbol 標準化 + yfinance OHLCV
│       ├── indicator_engine.py # RSI / MACD / BB / ATR / snapshot
│       ├── backtest_engine.py  # 4 策略 long-only 向量化回測
│       └── localizer.py        # 中英文輸出本地化
└── tests/                      # pytest, 純合成資料
    ├── conftest.py
    ├── test_agents.py
    ├── test_backtest_engine.py
    ├── test_indicator_engine.py
    ├── test_market_data.py
    └── test_localizer.py
```

---

## 🌐 支援市場

| 市場 | 輸入範例 | yfinance ticker |
|------|---------|----------------|
| 🇺🇸 美股 | `AAPL` `TSLA` `NVDA` | `AAPL` |
| 🇹🇼 台股 / ETF | `2330` `0050` `00878` | `2330.TW` |
| 🪙 加密（Binance 風格） | `BTCUSDT` `ETHUSDT` | `BTC-USD` |
| 已帶後綴 | `BTC-USD` `2330.TW` | （不變） |

Symbol 標準化邏輯：[app/services/market_data.py](app/services/market_data.py)

---

## 🤖 4-Agent 流程

`POST /analyze-symbol` 完整流程：

```
fetch_price_history()
   ↓
build_indicator_snapshot()  ← 計算 RSI/MACD/BB/ATR/MA/Fibonacci/swing
   ↓
TechnicalAgent  ─┐
NewsAgent       ─┼──→  RiskAgent  ──→  DecisionAgent  ──→  localize_output()
                 ┘                       (技術 70% + 新聞 30%)
```

最終輸出包含：`final_view`（signal / action / risk / confidence / summary）+ `trade_plan`（部位 / 進場偏好 / 時間框架 / 計畫）+ `agent_details`（各 agent 原始評分）

---

## 🔌 API Endpoints

| Method | Endpoint | 說明 |
|--------|---------|------|
| GET  | `/`                  | 健康/版本 |
| GET  | `/health`            | health check |
| POST | `/analyze`           | 手動輸入指標分析 |
| POST | `/analyze-symbol`    | 自動抓資料 + 完整 Agent 分析 |
| POST | `/analyze-watchlist` | 自選股批次分析（依信心排名） |
| POST | `/backtest`          | 單一策略回測 |
| POST | `/backtest-multi`    | 多策略比較（依 Sharpe 排名） |

範例：

```bash
curl -X POST http://localhost:8000/analyze-symbol \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","period":"6mo","language":"zh"}'

curl -X POST http://localhost:8000/backtest-multi \
  -H "Content-Type: application/json" \
  -d '{"symbol":"2330","period":"1y"}'
```

---

## 📈 技術指標

| 指標 | 參數 | 用途 |
|------|------|------|
| RSI | 14 | 超買 >70 / 超賣 <30 |
| MACD | 12/26/9 | histogram / 黃金死亡交叉偵測 |
| Bollinger Bands | 20, 2σ | %B / 上下軌 / Bandwidth squeeze |
| ATR | 14 | 平均真實波幅 |
| MA | 5 / 20 | 短期 / 長期均線 |
| Fibonacci | 23.6 / 38.2 / 50 / 61.8 / 78.6% | 從 swing high/low 計算（排除當日） |

調整評分閾值：直接改 [technical_agent.py](app/agents/technical_agent.py) 內的規則表（`PRICE_RULES`、`RSI_RULES` 等）。

---

## 🏗️ 回測策略

| 策略 key | 進場 | 出場 |
|---------|------|------|
| `ma_crossover` | 短均線 > 長均線 | 短均線 < 長均線 |
| `rsi` | RSI < 30 | RSI > 70 |
| `macd` | histogram > 0 | histogram < 0 |
| `bollinger` | 跌破下軌 | 突破上軌 |

皆 long-only 向量化、含手續費，輸出 Sharpe / 最大回撤 / 勝率 / 對 buy-and-hold 超額。

---

## 📰 News Agent 三種模式

由 `NEWS_AGENT_MODE` 環境變數切換：

- `keyword`（預設）— 純規則式中英文關鍵字計分，**免 API key**
- `gemini` — 呼叫 Google Gemini，失敗自動 fallback 到 keyword
- `claude` — 呼叫 Anthropic Claude，失敗自動 fallback 到 keyword

LLM 模式回傳的 JSON 用 brace-counting 抽取，可處理巢狀物件與輸出前後文字。

---

## ⚙️ 環境變數（`.env`）

```env
NEWS_AGENT_MODE=keyword
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
OPENAI_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-20250514
GEMINI_MODEL=gemini-2.5-flash
OPENAI_MODEL=gpt-4.1-mini
MA_SHORT_WINDOW=5
MA_LONG_WINDOW=20
VOLATILITY_WINDOW=10
SWING_WINDOW=20
```

---

## 🐳 Docker

```bash
docker build -t ai-quant-starter .
docker run -p 8000:8000 --env-file .env ai-quant-starter
```

---

## 🌏 多語輸出

請求帶 `"language": "zh"` 會在輸出中加入中譯欄位（`signal_label` / `action_label` / `summary_zh` / `trade_plan_note_zh` 等），原英文欄位保留。

---

## ⚠️ 免責聲明

本專案所有分析結果**僅供技術研究參考**，不構成任何投資建議。
投資有風險，請依自身風險承受能力謹慎決策。
