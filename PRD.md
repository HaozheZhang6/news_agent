# PRD: In-Car, Voice-Activated News Recommendation Agent

## 1. Background & Objectives
- **Problem**  
  Drivers lack a safe, hands-free way to stay up-to-date on global, local (US) and tech news—as well as market signals—while on the road.  
- **Goals**  
  1. Deliver bite-sized, voice-driven news briefs via an iOS app.  
  2. Support “Tell me more” and “Skip” via natural speech.  
  3. Continuously adapt to user preferences and watchlist stocks.

## 2. Scope

### 2.1 In-Scope (MVP)
- **Platform**: iOS smartphone app  
- **Voice & Interaction**:  
  - Wake-word → ASR → Intent → TTS (OpenAI-style interactive voice)  
  - Pure speech interaction  
- **Model**: GLM-4-Flash (cloud)  
  ```python
  from langchain.chat_models import ChatOpenAI
  import os

  model = ChatOpenAI(
      model="glm-4-flash",
      temperature=0,
      api_key=os.getenv("ZHIPUAI_API_KEY"),
      openai_api_base="https://open.bigmodel.cn/api/paas/v4/",
  )
````

* **Data Sources**:

  * News & sentiment: AlphaVantage free API
  * Stock data: `yfinance`
  * Categories: global big news, US big news, tech news
* **Memory**:

  * Short-term: 128 KB
  * Long-term: 128 KB
* **Agents**:

  1. **Aggregator**: fetch & summarize news/sentiment
  2. **Ranker**: score & order items (trainable later)

### 2.2 Out-of-Scope

* Visual dashboard beyond minimal playback indicators
* Real-time stock-price latency guarantees
* Multi-language support

## 3. User Stories

1. **Driver**: “Hey Agent, what’s the news?” → 20–30 sec briefing.
2. **Driver**: “Tell me more” → deep-dive on current item.
3. **Driver**: “Skip” → next item.
4. **Investor**: Prioritized updates on my watchlist stocks.

## 4. Functional Requirements

| ID | Requirement                                                                        |
| :- | :--------------------------------------------------------------------------------- |
| F1 | Wake-word detection + ASR tuned for in-car noise.                                  |
| F2 | OpenAI-style interactive TTS voice.                                                |
| F3 | News ingestion via AlphaVantage (headlines + sentiment) for global/US/tech.        |
| F4 | Stock/watchlist sync via `yfinance`.                                               |
| F5 | Memory manager (128 KB short/long-term).                                           |
| F6 | Dialog manager handling “more”, “skip”, “save for later”.                          |
| F7 | Background preference updates from explicit (likes) & implicit (skip/listen time). |
| F8 | Two-agent pipeline: Aggregator and Ranker.                                         |

## 5. System Architecture & Workflow

```mermaid
flowchart LR
  subgraph Voice Layer
    A[Wake-Word] --> B[ASR]
    B --> C[Intent & Slot Filler]
    C --> D[Dialog Manager]
    D --> E[TTS]
  end

  subgraph Agents
    subgraph Aggregator Agent
      F[Fetch: AlphaVantage news & sentiment]
      G[Fetch: yfinance tickers]
      H[Summarize via GLM-4-Flash]
      F & G --> H
    end
    subgraph Ranker Agent
      I[Score & rank summaries]
    end
    H --> I --> D
  end

  subgraph Memory
    J[Short-Term (128 KB)]
    K[Long-Term (128 KB)]
    D --> J
    D --> K
  end
```

## 6. Model Design

* **Base**: GLM-4-Flash (cloud-hosted)
* **Tasks**: summarization, intent classification, preference inference
* **Inference**: API calls; no strict latency SLA

## 7. Metrics & KPIs

* **Speech Recognition**

  * Word Error Rate (WER)
  * ASR latency
* **Engagement**

  * Listen-time per session
  * Deep-dive rate (`“Tell me more”` ratio)
  * Skip rate

## 8. Roadmap & Milestones

| Milestone | Scope                                                                     | Timeline |
| :-------- | :------------------------------------------------------------------------ | :------- |
| **M1**    | iOS app shell, wake-word + ASR + TTS pipeline, Aggregator Agent prototype | 4 weeks  |
| **M2**    | GLM-4-Flash summarization, memory mgmt, “more/skip” commands              | 6 weeks  |
| **M3**    | Ranker Agent, preference logging & feedback loop, KPI dashboards          | 8 weeks  |
