# ⚡ AI 量化交易平台

> 整合技術分析、基本面、新聞情緒的 AI 多 Agent 量化交易儀表板
> 支援美股、台股、台股 ETF、Binance 加密貨幣（現貨/永續）

---

## 🚀 快速啟動

```powershell
cd C:\Users\USER\OneDrive\Desktop\ai-quant-starter
.venv\Scripts\activate
uvicorn app.main:app --reload
```

瀏覽器開啟：http://localhost:8000

---

## 📁 專案結構

```
ai-quant-starter/
├── dashboard.html                  # 前端儀表板（單頁應用）
├── requirements.txt
├── .env                            # API Keys（不上傳 Git）
├── .env.example
├── Dockerfile
└── app/
    ├── main.py                     # FastAPI 主程式 + 所有 API Endpoints
    ├── config.py                   # 環境變數設定
    ├── orchestrator.py             # 分析流程協調核心
    ├── service.py
    ├── agents/
    │   ├── agent_base.py           # Agent 基底類別（AgentResult dataclass）
    │   ├── technical_agent.py      # 技術面規則 Agent（含中英文翻譯）
    │   ├── technical_agent_v2.py   # 技術面 AI Agent（LLM 解讀）
    │   ├── fundamental_agent.py    # 基本面 Agent（P/E、EPS、ROE）
    │   ├── news_agent.py           # 新聞面規則 Agent
    │   ├── news_agent_v2.py        # 新聞面 AI Agent
    │   ├── decision_agent.py       # 決策 Agent
    │   ├── risk_agent.py           # 風險 Agent
    │   └── multi_agent_orchestrator.py  # 多 Agent 協作 + LLM 辯論
    └── services/
        ├── market_data.py          # 統一市場資料（美股/台股/加密貨幣）
        ├── indicator_engine.py     # RSI/MACD/BB/ATR 計算
        ├── history_service.py      # K 線歷史資料 + 指標
        ├── entry_price_calculator.py  # 建議入場價位計算
        ├── stop_loss_calculator.py    # 停損停利計算
        ├── backtest_engine.py      # 回測引擎
        ├── fundamentals.py         # 財報基本面（yfinance）
        ├── llm_client.py           # 統一 LLM 介面（Claude / Gemini）
        ├── localizer.py            # 中英文本地化
        ├── multi_timeframe.py      # 多時間框架分析
        └── stop_loss_calculator.py # 停損停利計算
```

---

## 🌐 支援市場

| 市場 | 範例輸入 | 資料來源 |
|------|---------|---------|
| 🇺🇸 美股 | `AAPL` `TSLA` `NVDA` | yfinance |
| 🇹🇼 台股 | `2330` `2317` `2454` | yfinance (.TW) |
| 📊 台股 ETF | `0050` `0056` `00878` | yfinance (.TW) |
| 🪙 加密現貨 | `BTC` `ETHUSDT` `BTC/USDT` | Binance (ccxt) |
| 🪙 加密永續 | `BTCPERP` `ETH-PERP` | Binance (ccxt) |

---

## 📊 Dashboard 功能

### 搜尋列
- 下拉市場選擇：美股 / 台股 / 台股 ETF / 加密貨幣
- 點擊搜尋欄或切換市場時顯示熱門建議（各市場 20 支）
- 點選建議直接跳到總覽頁執行分析
- 台股自動補 `.TW`（純數字輸入）

### 頁籤

#### 📊 總覽
- 訊號 / 建議 / 現價 / 信心 四格卡
- Agent 評分條（技術面各指標加權分數）
- 交易計劃（倉位 / 出場 / 週期 / 風險）
- **即時指標面板**（RSI / MACD / 均線 / 布林 / ATR / 24H 高低）
- 即時停損停利建議

#### 📈 K 線圖
- 蠟燭圖 + MA / BB / 趨勢斜波
- **時間週期**：1分鐘 / 15分鐘 / 1小時 / 4小時 / 1日 / 15日 / 週線 / 1月
- **AI 自動斐波那契**：偵測最近關鍵 swing high/low 畫回撤線
- **手動繪製斐波那契**：點選任意兩點
- 主要結構（可選開關）
- 顯示根數滑桿 + 縮略時間軸導覽（可拖曳）
- 滾輪縮放 / 拖曳平移（TradingView 風格）
- Y 軸右側拖曳調整價格範圍
- 價格間距選擇（自動 / $1 / $5 / $10 / ... / $500）
- MACD / RSI 子圖（X 軸同步縮放）

#### 🎯 停損停利（入場建議）
- AI 入場建議卡（▲ 做多 / ▼ 做空 / ⚠ 減碼觀望 / ◈ 觀望）
- **建議入場價位區間**（結合 ATR / 均線 / 斐波那契 / 布林帶加權計算）
- 視覺化止盈止損階梯
- 六格數值卡（停損 / 目標一/二/三 / 風險報酬 / ATR）
- AI 分析理由

> **注意：** 股票只顯示做多/觀望，加密貨幣才有做空建議

#### 🕐 多時間框架
- 日 / 週 / 月 三週期共識

#### 📋 基本面
- P/E、EPS、ROE、營收成長等 12 項指標

#### 🔁 回測
- MA 交叉 / RSI / MACD / 布林 四策略比較 + 淨值曲線

#### 👁 自選股
- 熱力圖 + 排名表

---

## 🤖 AI 多 Agent 架構

```
使用者輸入
    ↓
Orchestrator Agent（協調）
    ↙        ↓        ↘
技術面     基本面     新聞面
Agent     Agent     Agent
(weight   (weight   (weight
  1.2)      0.8)      0.7)
    ↘        ↓        ↙
    加權投票 + LLM 辯論
         ↓
    最終投資建議
         ↓
    儲存至 DB（待實作）
```

### 三個 Agent

| Agent | 資料來源 | 評分依據 |
|-------|---------|---------|
| TechnicalAgentV2 | RSI / MACD / BB / MA / ATR / Fibonacci | 規則評分 + Claude/Gemini 解讀 |
| FundamentalAgent | P/E / EPS / ROE / 營收成長 / 負債比 | 規則評分 + AI 解讀 |
| NewsAgentV2 | 新聞文字 / AI 背景知識 | 情緒分析 + AI 解讀 |

### 辯論流程
三個 Agent 平行執行 → 加權投票 → LLM 扮演資深組合經理整合共識

---

## 🔌 API Endpoints

| Method | Endpoint | 說明 |
|--------|---------|------|
| POST | `/full-analysis` | 完整分析（技術+基本面+多時間框架+停損停利+入場建議）|
| POST | `/analyze` | 手動輸入指標分析 |
| POST | `/analyze-symbol` | 自動抓取分析 |
| POST | `/analyze-watchlist` | 批次自選股分析 |
| POST | `/multi-agent` | 多 Agent 協作分析 |
| POST | `/backtest` | 單策略回測 |
| POST | `/backtest-multi` | 多策略比較 |
| POST | `/stop-loss` | 停損停利計算 |
| POST | `/multi-timeframe` | 多時間框架 |
| GET | `/history/{symbol}` | K 線歷史資料 + 指標 |
| GET | `/price/{symbol}` | 即時價格（股票/加密通用）|
| GET | `/live-snapshot/{symbol}` | 即時指標快照（30-60秒更新）|
| GET | `/fundamentals/{symbol}` | 財報基本面 |
| GET | `/search/crypto` | 搜尋 Binance 交易對 |
| GET | `/market-type/{symbol}` | 自動判斷市場類型 |

---

## 📈 技術指標

| 指標 | 參數 | 說明 |
|------|------|------|
| RSI | 14 | 超買 >70 / 超賣 <30 |
| MACD | 12/26/9 | 柱狀圖 / 黃金死亡交叉 |
| Bollinger Bands | 20, 2σ | 上軌 / 中軌 / 下軌 / %B |
| ATR | 14 | 平均真實波幅 |
| MA | 5 / 20 | 短期 / 長期均線 |
| Fibonacci | 23.6 / 38.2 / 50 / 61.8 / 78.6% | 回撤支撐壓力 |

---

## 🏗️ 回測策略

| 策略 | 說明 |
|------|------|
| `ma_crossover` | MA 黃金 / 死亡交叉 |
| `rsi` | RSI 超買超賣 |
| `macd` | MACD histogram |
| `bollinger` | Bollinger 均值回歸 |

---

## ⚙️ 環境設定

`.env` 檔案：

```env
ANTHROPIC_API_KEY=your_claude_api_key
GEMINI_API_KEY=your_gemini_api_key
NEWS_AGENT_MODE=claude   # claude 或 gemini
CLAUDE_MODEL=claude-opus-4-5
GEMINI_MODEL=gemini-2.0-flash
```

---

## 📦 安裝依賴

```powershell
pip install fastapi uvicorn pydantic google-genai yfinance pandas numpy anthropic openai python-dotenv ccxt requests
```

---

## 🗺️ 開發路線圖

- [x] FastAPI 後端架構
- [x] K 線圖（蠟燭棒 / 縮放 / 斐波那契 / 趨勢線）
- [x] 多時間週期（1分 / 15分 / 1時 / 4時 / 1日 / 15日 / 週 / 月）
- [x] 即時價格更新（美股 15秒 / 加密 5秒）
- [x] 即時指標面板（60秒更新）
- [x] 多 Agent 協作（技術 + 基本面 + 新聞）
- [x] 加密貨幣（Binance ccxt）整合
- [x] 停損停利計算器
- [x] 建議入場價位（ATR + 均線 + Fibonacci 加權）
- [x] 回測引擎（4 策略）
- [x] 基本面資料
- [x] 自選股熱力圖
- [x] 熱門股建議下拉（美股 / 台股 / 台股 ETF / 加密）
- [x] 中英文語言切換
- [ ] SQL 資料庫整合（儲存分析結果 / 自選股 / 回測記錄）
- [ ] 期貨支援（加密永續已部分實作）
- [ ] 推播通知（價格到達目標位）
- [ ] 使用者帳號系統

---

## ⚠️ 免責聲明

本平台所有分析結果僅供技術研究參考，**不構成任何投資建議**。
投資有風險，請依自身風險承受能力謹慎決策。

---

*Last updated: 2026-04-20*
