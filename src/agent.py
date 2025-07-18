from langchain_openai import ChatOpenAI
from langchain.agents import tool, AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
import yfinance as yf
from alpha_vantage.alphaintelligence import AlphaIntelligence
import asyncio
import json

from . import config
from .memory import load_preferences, save_preferences

@tool
def get_stock_price(ticker: str) -> str:
    """Fetches the latest stock price for a given ticker."""
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1d")
    if hist.empty:
        return f"Could not find stock price for {ticker}."
    latest_price = hist['Close'].iloc[-1]
    return f"The latest stock price for {ticker} is ${latest_price:.2f}."

@tool
def get_news_headlines(topics: str = None) -> list[dict]:
    """    Fetches news headlines. Can be filtered by topics like 'technology', 'earnings', 'ipo', 'mergers_and_acquisitions', 'financial_markets', 'economy_fiscal', 'economy_monetary', 'economy_macro', 'energy', 'blockchain', 'retail_wholesale', 'manufacturing', 'real_estate'.
    If no topics are specified, it will fetch general news.
    Returns a list of dictionaries, each containing 'title' and 'summary' of a news item.
    """
    try:
        ai = AlphaIntelligence(key=config.ALPHAVANTAGE_API_KEY, output_format='pandas')
        news_df, _ = ai.get_news_sentiment(topics=topics, limit=5)
        if news_df.empty:
            return []

        news_items = []
        for index, row in news_df.iterrows():
            news_items.append({
                'title': row['title'],
                'summary': row['summary']
            })
        return news_items
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

class NewsAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="glm-4-flash",
            temperature=0,
            api_key=config.ZHIPUAI_API_KEY,
            openai_api_base="https://open.bigmodel.cn/api/paas/v4/",
        )
        
        # Load user preferences
        self.preferences = load_preferences()
        self.preferred_topics = self.preferences.get("preferred_topics", [])
        self.watchlist_stocks = self.preferences.get("watchlist_stocks", [])

        @tool
        def add_preferred_topic(topic: str) -> str:
            """Adds a news topic to the user's preferred topics list."""
            if topic.lower() not in [t.lower() for t in self.preferred_topics]:
                self.preferred_topics.append(topic)
                self.preferences["preferred_topics"] = self.preferred_topics
                save_preferences(self.preferences)
                return f"Added '{topic}' to your preferred topics."
            return f"'{topic}' is already in your preferred topics."

        @tool
        def remove_preferred_topic(topic: str) -> str:
            """Removes a news topic from the user's preferred topics list."""
            original_len = len(self.preferred_topics)
            self.preferred_topics = [t for t in self.preferred_topics if t.lower() != topic.lower()]
            if len(self.preferred_topics) < original_len:
                self.preferences["preferred_topics"] = self.preferred_topics
                save_preferences(self.preferences)
                return f"Removed '{topic}' from your preferred topics."
            return f"'{topic}' was not found in your preferred topics."

        @tool
        def get_preferred_topics() -> str:
            """Returns the list of user's preferred news topics."""
            if self.preferred_topics:
                return f"Your preferred topics are: {', '.join(self.preferred_topics)}."
            return "You don't have any preferred topics set yet."

        @tool
        def add_watchlist_stock(ticker: str) -> str:
            """Adds a stock ticker to the user's watchlist."""
            if ticker.upper() not in [s.upper() for s in self.watchlist_stocks]:
                self.watchlist_stocks.append(ticker.upper())
                self.preferences["watchlist_stocks"] = self.watchlist_stocks
                save_preferences(self.preferences)
                return f"Added '{ticker.upper()}' to your watchlist."
            return f"'{ticker.upper()}' is already in your watchlist."

        @tool
        def remove_watchlist_stock(ticker: str) -> str:
            """Removes a stock ticker from the user's watchlist."""
            original_len = len(self.watchlist_stocks)
            self.watchlist_stocks = [s for s in self.watchlist_stocks if s.upper() != ticker.upper()]
            if len(self.watchlist_stocks) < original_len:
                self.preferences["watchlist_stocks"] = self.watchlist_stocks
                save_preferences(self.preferences)
                return f"Removed '{ticker.upper()}' from your watchlist."
            return f"'{ticker.upper()}' was not found in your watchlist."

        @tool
        def get_watchlist_stocks() -> str:
            """Returns the list of user's watchlist stocks."""
            if self.watchlist_stocks:
                return f"Your watchlist stocks are: {', '.join(self.watchlist_stocks)}."
            return "You don't have any stocks in your watchlist yet."

        self.tools = [
            get_stock_price,
            get_news_headlines,
            add_preferred_topic,
            remove_preferred_topic,
            get_preferred_topics,
            add_watchlist_stock,
            remove_watchlist_stock,
            get_watchlist_stocks
        ]
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that provides news and stock prices. You can also manage user preferences for news topics and stock watchlists. When asked for news, use the 'get_news_headlines' tool. After getting the raw news, you will rephrase it for the user. Use the preference management tools when the user asks to add, remove, or list their preferred topics or watchlist stocks."),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        self.news_cache = {} # Cache for deep-dive summaries: {index: deep_dive_text}
        self.current_news_items = [] # Store raw news items for processing
        self.memory = [] # Short-term memory for conversational context

    async def _rephrase_news_item(self, news_item: dict, rephrase_type: str) -> str:
        """Rephrases a news item for either a brief or deep-dive summary using the LLM."""
        if rephrase_type == "brief":
            prompt_template = f"Summarize the following news item into a concise, one-sentence brief suitable for a voice assistant. Title: {news_item['title']}. Summary: {news_item['summary']}"
        elif rephrase_type == "deep_dive":
            prompt_template = f"Explain the key points of the following news item in a detailed but brief paragraph, about 3-4 sentences long. Title: {news_item['title']}. Summary: {news_item['summary']}"
        else:
            return "Invalid rephrase type."

        response = await self.llm.ainvoke(prompt_template)
        return response.content

    async def process_fetched_news(self, raw_news_items: list[dict]) -> str:
        """Processes raw news items, generates briefs, and asynchronously caches deep-dives."""
        self.current_news_items = raw_news_items
        self.news_cache = {} # Clear cache for new news

        brief_summaries = []
        deep_dive_tasks = []

        for i, item in enumerate(raw_news_items):
            # Generate brief summary immediately
            brief = await self._rephrase_news_item(item, "brief")
            brief_summaries.append(f"{i+1}. {brief}")

            # Asynchronously generate deep-dive and cache it
            deep_dive_task = asyncio.create_task(self._rephrase_news_item(item, "deep_dive"))
            deep_dive_tasks.append((i, deep_dive_task))
        
        # Store deep-dive tasks for later retrieval (e.g., in main loop)
        # For now, we'll just await them here to ensure they are done for caching
        for i, task in deep_dive_tasks:
            self.news_cache[i] = await task

        return "Here are the latest news headlines:\n" + "\n".join(brief_summaries)

    async def get_response(self, user_input: str) -> str:
        """Generates a response from the agent based on user input."""
        # Add user input to memory
        self.memory.append(HumanMessage(content=user_input))

        # Pass memory to the agent executor
        response = await self.agent_executor.ainvoke({"input": user_input, "chat_history": self.memory})
        
        # Add agent response to memory
        self.memory.append(AIMessage(content=response['output']))

        # Check if the agent used the get_news_headlines tool
        # This is a heuristic based on the verbose output. A more robust way would be custom callbacks.
        if "Calling tool `get_news_headlines`" in response['output']:
            # The actual news data is not directly in response['output'] for tool calls.
            # It's usually in intermediate_steps. We need to parse the verbose output.
            # For now, let's assume the LLM will then summarize the news it got.
            # This part needs to be refined for the actual news processing flow.
            # A better way is to have the tool return the data, and the agent then processes it.

            # Let's assume for now that if the agent *intended* to get news, we will process it.
            # This requires a change in how the agent_executor returns tool outputs.
            # For now, I'll make a direct call to get_news_headlines if the input suggests it.
            # This bypasses the agent's decision for news, but allows us to test the rephrasing.
            # This is a temporary simplification for testing the rephrasing and caching.

            # Reverting to the original plan: AgentExecutor calls the tool, and we process its output.
            # The `response['output']` from AgentExecutor will be the LLM's final string response.
            # We need to extract the raw news from `intermediate_steps` if the tool was called.

            raw_news_data = None
            for step in response.get('intermediate_steps', []):
                if isinstance(step, tuple) and len(step) == 2 and hasattr(step[0], 'tool') and step[0].tool == 'get_news_headlines':
                    try:
                        # The tool output is a string representation of a list of dicts
                        raw_news_data = json.loads(step[1])
                        break
                    except json.JSONDecodeError:
                        print(f"Could not decode news data: {step[1]}")
                        raw_news_data = []
                        break
            
            if raw_news_data:
                return await self.process_fetched_news(raw_news_data)
            else:
                return response['output'] # Fallback if news tool was called but no data extracted
        
        return response['output']

    def get_deep_dive(self, index: int) -> str:
        """Retrieves a cached deep-dive summary by index."""
        return self.news_cache.get(index, "Deep-dive not available for this item.")