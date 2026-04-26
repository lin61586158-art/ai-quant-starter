# AI 量化交易 API — Claude Code 專案指引

## 專案概述
FastAPI 多 Agent 量化分析後端（純 API，無前端）。
4 個 Agent 串接：技術面 → 新聞面 → 風險評估 → 決策整合。
支援美股 / 台股 / 台股ETF / 加密貨幣（皆透過 yfinance 抓資料）。

## 快速啟動
```bash
pip install -r requirements.txt
cp .env.example .env   # 填 API Keys（純跑 keyword 模式可不填）
uvicorn app.main:app --reload
# http://localhost:8000/docs
pytest                 # 跑測試
```

## 實際專案結構
```
ai-quant-starter2/
├── requirements.txt
├── .env.example
├── CLAUDE.md
├── app/
│   ├── main.py                 # FastAPI endpoints
│   ├── config.py               # 環境變數
│   ├── orchestrator.py         # 流程協調
│   ├── agents/
│   │   ├── technical_agent.py  # 9 指標評分（規則表驅動）
│   │   ├── news_agent.py       # keyword / gemini / claude 三模式
│   │   ├── risk_agent.py       # 風險等級判定
│   │   └── decision_agent.py   # 最終訊號 + 交易計畫
│   └── services/
│       ├── market_data.py          # symbol 標準化 + yfinance 抓 OHLCV
│       ├── indicator_engine.py     # RSI / MACD / BB / ATR / snapshot
│       ├── backtest_engine.py      # 4 策略 long-only 向量化回測
│       └── localizer.py            # 中英文輸出本地化
└── tests/
    ├── conftest.py             # 共用 OHLCV fixtures
    ├── test_agents.py
    ├── test_backtest_engine.py
    ├── test_indicator_engine.py
    ├── test_market_data.py
    └── test_localizer.py
```

## API Endpoints

| Method | Endpoint | 說明 |
|--------|----------|------|
| GET  | `/`                   | 健康/版本 |
| GET  | `/health`             | health check |
| POST | `/analyze`            | 手動輸入指標分析 |
| POST | `/analyze-symbol`     | 自動抓資料 + 完整 Agent 分析 |
| POST | `/analyze-watchlist`  | 自選股批次分析（依信心排名） |
| POST | `/backtest`           | 單一策略回測 |
| POST | `/backtest-multi`     | 多策略比較（依 Sharpe 排名） |

回測支援策略：`ma_crossover` | `rsi` | `macd` | `bollinger`（皆 long-only）

## 支援市場（由 [normalize_symbol](app/services/market_data.py) 處理）

| 市場 | 輸入範例 | 標準化後 |
|------|---------|---------|
| 🇺🇸 美股 | `AAPL` | `AAPL` |
| 🇹🇼 台股 / ETF | `2330`, `0050` | `2330.TW`, `0050.TW` |
| 🪙 加密 (Binance) | `BTCUSDT`, `ETHUSDT` | `BTC-USD`, `ETH-USD` |
| 已帶後綴 | `BTC-USD`, `2330.TW` | 不變 |

## Agent 流程

[run_symbol_analysis](app/orchestrator.py#L120) 流程：
1. `fetch_price_history` 抓 OHLCV
2. `build_indicator_snapshot` 算所有指標 → snapshot dict
3. `run_technical_agent` 給技術分數 / signal
4. `run_news_agent` 給情緒分數 / 事件 tags
5. `run_risk_agent` 結合上述輸出風險等級
6. `run_decision_agent` 加權合成 → final_view + trade_plan
7. `localize_output` 視 `language` 參數中譯

技術面權重 70%，新聞面 30%（[decision_agent.py:33](app/agents/decision_agent.py#L33)）

## News Agent 模式（由 `NEWS_AGENT_MODE` 切換）

- `keyword`（預設）— 純規則式關鍵字計分，免 API key
- `gemini` — 呼叫 Gemini，失敗自動 fallback 到 keyword
- `claude` — 呼叫 Anthropic Claude，失敗自動 fallback 到 keyword

JSON 抽取使用 brace-counting，可處理巢狀物件與 LLM 輸出前後文字。

## 環境變數（.env）
```
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

## 常見修改場景

### 新增 Endpoint
在 [app/main.py](app/main.py) 末尾加 Pydantic Request model 和 handler。

### 調整技術面評分閾值
[technical_agent.py](app/agents/technical_agent.py) 的規則表（`PRICE_RULES`、`RSI_RULES`、`VOLATILITY_RULES` 等）—直接改 tuple 即可，邏輯不必動。

### 新增技術指標
1. 在 [indicator_engine.py](app/services/indicator_engine.py) 加計算函式
2. 在 `build_indicator_snapshot` 加進 snapshot 輸出
3. 在 [technical_agent.py](app/agents/technical_agent.py) 加規則表 + `_apply` 一行
4. 補對應測試

### 新增回測策略
在 [backtest_engine.py](app/services/backtest_engine.py)：
1. 寫 `_signals_xxx(df) -> pd.Series` 回傳 0/1/-1
2. 註冊到 `_STRATEGY_FUNCS` 與 `SUPPORTED_STRATEGIES`

### 新增中文翻譯
在 [localizer.py](app/services/localizer.py) 對應 MAP 加 entry。

## 注意事項

1. **加密走 yfinance 不是 ccxt**——symbol 會被轉成 `BTC-USD` 風格
2. **回測至少需 60 根 K 線**（`run_backtest` 強制）
3. **swing 區間排除當日**（[indicator_engine.py](app/services/indicator_engine.py)）——避免「price > swing_high」永遠成立
4. **首次加新指標記得補 snapshot 與測試**，不然 `analyze-symbol` 會少傳值
5. **News LLM 模式失敗會自動退化到 keyword**，記得看 `news_mode` 欄位確認
6. **`.env` 不要 commit**

## 測試
```bash
pytest             # 全部
pytest tests/test_indicator_engine.py -v
pytest -k news     # 只跑 news 相關
```
所有測試使用 `conftest.py` 內的合成 OHLCV，**不依賴外網**。
