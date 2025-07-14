# In-Car, Voice-Activated News Recommendation Agent

## 1. Overview

This project is a voice-activated news recommendation agent for iOS, designed for drivers. It provides a safe, hands-free way to consume news briefs covering global, US, and tech stories, as well as personalized stock market updates. The agent is designed to be interactive, responding to voice commands like "tell me more" or "skip," and it learns from user behavior to personalize the news feed.

## 2. Features (MVP)

- **Voice-First Interface**: All interactions are designed to be hands-free, using a wake-word and natural language commands.
- **Multi-Source Aggregation**: Fetches news and sentiment from **AlphaVantage** and stock data from **yfinance**.
- **Personalized Content**:
    - Covers global news, US news, and tech news.
    - Tracks a user-defined watchlist of stocks.
- **Interactive Playback**: Users can ask for a deeper dive on a topic or skip to the next item.
- **Adaptive Ranking**: The agent continuously learns from explicit and implicit feedback to rank and prioritize news items.
- **Platform**: iOS

## 3. System Architecture

The system is composed of three main layers:

1.  **Voice Layer**: Handles all user audio interaction, from wake-word detection and Automatic Speech Recognition (ASR) to intent classification and Text-to-Speech (TTS) responses.
2.  **Agent Layer**:
    - **Aggregator Agent**: Fetches and summarizes news and stock data using the GLM-4-Flash model.
    - **Ranker Agent**: Scores and ranks the summarized items based on user preferences.
3.  **Memory Layer**: Maintains short-term and long-term user preferences to inform the Ranker Agent.

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

## 4. Roadmap

| Milestone | Scope                                                                     |
| :-------- | :------------------------------------------------------------------------ |
| **M1**    | iOS app shell, wake-word + ASR + TTS pipeline, Aggregator Agent prototype |
| **M2**    | GLM-4-Flash summarization, memory mgmt, “more/skip” commands              |
| **M3**    | Ranker Agent, preference logging & feedback loop, KPI dashboards          |