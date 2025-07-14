from langchain_openai import ChatOpenAI
from langchain.agents import tool, AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
import yfinance as yf
from alpha_vantage.alphaintelligence import AlphaIntelligence

from . import config

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
def get_news_headlines(topics: str = None) -> str:
    """    Fetches news headlines. Can be filtered by topics like 'technology', 'earnings', 'ipo', 'mergers_and_acquisitions', 'financial_markets', 'economy_fiscal', 'economy_monetary', 'economy_macro', 'energy', 'blockchain', 'retail_wholesale', 'manufacturing', 'real_estate'.
    If no topics are specified, it will fetch general news.
    """
    try:
        ai = AlphaIntelligence(key=config.ALPHAVANTAGE_API_KEY, output_format='pandas')
        news_df, _ = ai.get_news_sentiment(topics=topics, limit=5)
        if news_df.empty:
            return "No news found for the given topics."

        headlines = []
        for index, row in news_df.iterrows():
            headlines.append(f"- {row['title']}: {row['summary']}")
        
        return "\n".join(headlines)
    except Exception as e:
        return f"An error occurred while fetching news: {e}"

class NewsAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="glm-4-flash",
            temperature=0,
            api_key=config.ZHIPUAI_API_KEY,
            openai_api_base="https://open.bigmodel.cn/api/paas/v4/",
        )
        self.tools = [get_stock_price, get_news_headlines]
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that provides news and stock prices."),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    def get_response(self, user_input):
        """Generates a response from the agent based on user input."""
        response = self.agent_executor.invoke({"input": user_input})
        return response['output']
