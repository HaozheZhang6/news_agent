# In-Car, Voice-Activated News Recommendation Agent

## 1. Overview

This project is a voice-activated news recommendation agent, initially developed as a CLI application, with a future vision for an iOS app. It provides a safe, hands-free way for drivers to consume personalized news briefs covering global, US, and tech stories, as well as stock market updates. The agent is designed for natural, interruptible voice interaction and continuously learns from user behavior to personalize the news feed.

## 2. Features (MVP)

- **Voice-First & Interruptible Interface**: All interactions are hands-free, using a wake-word and natural language commands. Users can interrupt the agent at any time to issue new commands.
- **High-Quality TTS**: Utilizes a natural-sounding Text-to-Speech (TTS) engine (initially Edge-TTS) for a pleasant listening experience.
- **Intelligent News Rephrasing**: News summaries from APIs are rephrased and condensed by an AI agent for concise voice briefings. Deep-dive explanations are also pre-generated for instant access.
- **Multi-Source Aggregation**: Fetches news and sentiment from **AlphaVantage** and stock data from **yfinance**.
- **Personalized Content**:
    - Covers global news, US news, and tech news.
    - Tracks a user-defined watchlist of stocks.
- **Interactive Playback**: Users can ask for a deeper dive on a topic or skip to the next item.
- **Adaptive Ranking**: The agent continuously learns from explicit and implicit feedback to rank and prioritize news items.

## 3. System Architecture

The system is composed of three main layers:

1.  **Voice Layer**: Handles all user audio interaction, from wake-word detection and Automatic Speech Recognition (ASR) to intent classification and interruptible Text-to-Speech (TTS) responses.
2.  **Agent Layer**:
    - **Aggregator Agent**: Fetches raw news and stock data.
    - **Rephraser Agent**: Utilizes the GLM-4-Flash model to rephrase and summarize news for voice delivery (both brief and deep-dive versions, with deep-dives pre-generated asynchronously).
    - **Ranker Agent**: Scores and ranks the summarized items based on user preferences.
3.  **Memory Layer**: Maintains short-term and long-term user preferences to inform the Ranker Agent and store cached deep-dive summaries.

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

## 4. Roadmap

| Milestone | Scope                                                                     |
| :-------- | :------------------------------------------------------------------------ |
| **M1**    | CLI app shell, wake-word + ASR + TTS pipeline (Edge-TTS), Aggregator Agent prototype, Rephraser Agent (briefs only) |
| **M2**    | GLM-4-Flash summarization, memory mgmt, “more/skip” commands, Async deep-dive caching, Interruptible TTS |
| **M3**    | Ranker Agent, preference logging & feedback loop, KPI dashboards, iOS app shell |
