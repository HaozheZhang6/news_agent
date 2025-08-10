# PRD: In-Car, Voice-Activated News Recommendation Agent

## 1. Background & Objectives
- **Problem**  
  Drivers lack a safe, hands-free way to stay up-to-date on global, local (US) and tech news—as well as market signals—while on the road.  
- **Goals**  
  1. Deliver bite-sized, voice-driven news briefs via an iOS app.
  2. Support natural, interruptible interaction (e.g., “Tell me more,” “Skip,” or breaking in).
  3. Continuously adapt to user preferences and watchlist stocks.

## 2. Scope

### 2.1 In-Scope (MVP)
- **Platform**: CLI (initial v0.0.1 for core logic), eventually iOS smartphone app  
- **Voice & Interaction**:  
  - Wake-word → ASR → Intent → TTS (High-quality, natural voice)
  - **Real-time Interruption**: <50ms response to "stop", <30ms for "tell me more"
  - **Parallel Processing**: Continuous listener + speaker processes with 10ms command polling
  - Pure speech interaction with anytime interruption capability
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
  ```

* **Data Sources**: 
  * News & sentiment: AlphaVantage free API
  * Stock data: `yfinance`
  * Categories: global big news, US big news, tech news
* **Memory**: 
  * Short-term: 128 KB
  * Long-term: 128 KB
* **Agents**: 
  1. **Aggregator**: fetch & summarize news/sentiment
  2. **Rephraser**: rephrase and summarize news for voice delivery (brief & deep-dive)
  3. **Ranker**: score & order items (trainable later)

### 2.2 Out-of-Scope

* Visual dashboard beyond minimal playback indicators
* Real-time stock-price latency guarantees
* Multi-language support

## 3. User Stories

1. **Driver**: "Hey Agent, what's the news?" → 20–30 sec briefing.
2. **Driver**: "Tell me more" → **Instant interruption** + deep-dive on current item (<30ms transition).
3. **Driver**: "Skip" → next item with seamless navigation.
4. **Driver**: "Stop" → **Immediate halt** of current speech (<50ms response).
5. **Driver**: Interrupts mid-sentence at any time → Command processed within 10ms.
6. **Investor**: Prioritized updates on my watchlist stocks with interrupt capability.

## 4. Functional Requirements

| ID | Requirement                                                                        |
| :- | :--------------------------------------------------------------------------------- |
| F1 | Wake-word detection + ASR tuned for in-car noise.                                  |
| F2 | High-quality, natural, and interruptible TTS voice (e.g., Edge-TTS, with OpenAI TTS as future option). |
| F3 | News ingestion via AlphaVantage (headlines + sentiment) for global/US/tech.        |
| F4 | Stock/watchlist sync via `yfinance`.                                               |
| F5 | Memory manager (128 KB short/long-term).                                           |
| F6 | **Real-time Dialog Manager**: "more", "skip", "stop" with <50ms interruption response. |
| F7 | Background preference updates from explicit (likes) & implicit (skip/listen time). |
| F8 | Three-agent pipeline: Aggregator, Rephraser, and Ranker.                           |
| F9 | Asynchronous pre-generation and caching of deep-dive news summaries.               |

## 5. System Architecture & Workflow

```mermaid
flowchart LR
  subgraph Voice Layer
    A[Wake-Word] --> B[ASR]
    B --> C[Intent & Slot Filler]
    C --> D[Dialog Manager]
    D --> E[TTS (Interruptible)]
  end

  subgraph Agents
    subgraph Aggregator Agent
      F[Fetch: AlphaVantage news & sentiment]
      G[Fetch: yfinance tickers]
      F & G --> H[Raw News/Data]
    end
    subgraph Rephraser Agent
      H --> I[Summarize/Rephrase via GLM-4-Flash (Brief)]
      H --> J[Summarize/Rephrase via GLM-4-Flash (Deep-Dive, Async)]
    end
    subgraph Ranker Agent
      I & J --> K[Score & rank summaries]
    end
    K --> D
  end

  subgraph Memory
    L[Short-Term (128 KB)]
    M[Long-Term (128 KB)]
    D --> L
    D --> M
    J --> L
  end
```

## 6. Model Design

* **Base**: GLM-4-Flash (cloud-hosted)
* **Tasks**: summarization, intent classification, preference inference, rephrasing
* **Inference**: API calls; no strict latency SLA (except for pre-generated deep-dives)

## 7. Metrics & KPIs

* **Speech Recognition**
  * Word Error Rate (WER)
  * ASR latency
* **Engagement**
  * Listen-time per session
  * Deep-dive rate (`"Tell me more"` ratio)
  * Skip rate
  * **Interruption Response Time** (<50ms target)
  * **Command Processing Latency** (<10ms target)
  * Interruption rate (to measure naturalness of interaction)

## 8. Roadmap & Milestones

| Milestone | Scope                                                                     | Timeline |
| :-------- | :------------------------------------------------------------------------ | :------- |
| **M1**    | CLI app shell, wake-word + ASR + TTS pipeline (Edge-TTS), Aggregator Agent prototype, Rephraser Agent (briefs only) | 4 weeks  |
| **M2**    | GLM-4-Flash summarization, memory mgmt, “more/skip” commands, Async deep-dive caching, Interruptible TTS | 6 weeks  |
| **M3**    | Ranker Agent, preference logging & feedback loop, KPI dashboards, iOS app shell | 8 weeks  |