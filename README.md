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

## 5. How to Use

### 5.1. Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd News_agent
    ```
2.  **Create a virtual environment and install dependencies:**
    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
    ```
3.  **Configure API Keys:**
    Create a `.env` file in the root directory of the project with your API keys:
    ```
    ZHIPUAI_API_KEY="YOUR_ZHIPUAI_API_KEY"
    ALPHAVANTAGE_API_KEY="YOUR_ALPHAVANTAGE_API_KEY"
    ```
    Replace `YOUR_ZHIPUAI_API_KEY` and `YOUR_ALPHAVANTAGE_API_KEY` with your actual keys.

### 5.2. Running the Agent

To start the voice-activated news agent, run the following command from the project root:

```bash
source .venv/bin/activate
python -m src.main
```

### 5.3. Voice Commands

Once the agent starts, it will greet you. You can then use the following voice commands:

*   **General News:**
    *   "What's the news?"
    *   "Tell me what's happening."
    *   "Latest news."

*   **News by Topic:**
    *   "Tell me the news about technology."
    *   "Any news on financial markets?"
    *   "What's happening in the economy?"

*   **Stock Prices:**
    *   "What's the stock price of Apple?"
    *   "How much is NVDA?"
    *   "Tell me about Tesla stock."

*   **News Interaction:**
    *   "Tell me more" (while a news brief is playing, to get a deep-dive summary).
    *   "Skip" (to move to the next news brief).

*   **Preference Management:**
    *   "Add [topic] to my preferred topics." (e.g., "Add sports to my preferred topics.")
    *   "Remove [topic] from my preferred topics." (e.g., "Remove politics from my preferred topics.")
    *   "What are my preferred topics?"
    *   "Add [stock ticker] to my watchlist." (e.g., "Add GOOG to my watchlist.")
    *   "Remove [stock ticker] from my watchlist." (e.g., "Remove MSFT from my watchlist.")
    *   "What are my watchlist stocks?"

*   **Exiting:**
    *   "Exit"
    *   "Quit"