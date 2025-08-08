import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import json
from src.agent import NewsAgent, get_stock_price, get_news_headlines

# Mock external dependencies
@pytest.fixture
def mock_llm():
    with patch('src.agent.ChatOpenAI') as MockChatOpenAI:
        mock_instance = MockChatOpenAI.return_value
        mock_instance.ainvoke = AsyncMock(return_value=MagicMock(content="Rephrased summary"))
        yield mock_instance

@pytest.fixture
def mock_yfinance():
    with patch('src.agent.yf') as MockYFinance:
        mock_ticker = MockYFinance.Ticker.return_value
        # Mock history to return a DataFrame-like object with a 'Close' column
        mock_history_df = MagicMock()
        mock_history_df.empty = False
        mock_history_df.__getitem__.return_value.iloc.__getitem__.return_value = 150.00 # Direct float value
        mock_ticker.history.return_value = mock_history_df
        yield MockYFinance

@pytest.fixture
def mock_alpha_intelligence():
    with patch('src.agent.AlphaIntelligence') as MockAlphaIntelligence:
        mock_instance = MockAlphaIntelligence.return_value
        # Mock get_news_sentiment to return a DataFrame-like object
        mock_news_df = MagicMock()
        mock_news_df.empty = False
        
        # Create mock row objects that behave like dictionaries
        mock_row1 = MagicMock()
        mock_row1.__getitem__.side_effect = lambda key: {'title': 'Test News 1', 'summary': 'Summary of test news 1.'}[key]
        mock_row2 = MagicMock()
        mock_row2.__getitem__.side_effect = lambda key: {'title': 'Test News 2', 'summary': 'Summary of test news 2.'}[key]

        mock_news_df.iterrows.return_value = [
            (0, mock_row1),
            (1, mock_row2),
        ]
        mock_instance.get_news_sentiment.return_value = (mock_news_df, None)
        yield MockAlphaIntelligence

@pytest.fixture
def mock_memory_functions():
    with patch('src.agent.load_preferences') as mock_load,\
         patch('src.agent.save_preferences') as mock_save:
        mock_load.return_value = {'preferred_topics': [], 'watchlist_stocks': []}
        yield mock_load, mock_save

@pytest.mark.asyncio
async def test_get_stock_price_success(mock_yfinance):
    price = get_stock_price("AAPL")
    assert "$150.00" in price
    mock_yfinance.Ticker.assert_called_once_with("AAPL")
    mock_yfinance.Ticker.return_value.history.assert_called_once_with(period="1d")

@pytest.mark.asyncio
async def test_get_stock_price_not_found(mock_yfinance):
    mock_yfinance.Ticker.return_value.history.return_value.empty = True # Set empty to True for this test
    price = get_stock_price("UNKNOWN")
    assert "Could not find stock price for UNKNOWN." in price

@pytest.mark.asyncio
async def test_get_news_headlines_success(mock_alpha_intelligence):
    news = get_news_headlines("technology")
    assert len(news) == 2
    assert news[0]['title'] == 'Test News 1'
    mock_alpha_intelligence.assert_called_once()
    mock_alpha_intelligence.return_value.get_news_sentiment.assert_called_once_with(topics="technology", limit=5)

@pytest.mark.asyncio
async def test_get_news_headlines_empty(mock_alpha_intelligence):
    mock_alpha_intelligence.return_value.get_news_sentiment.return_value = (MagicMock(empty=True), None)
    news = get_news_headlines("empty_topic")
    assert len(news) == 0

@pytest.mark.asyncio
async def test_news_agent_init(mock_llm, mock_memory_functions):
    agent = NewsAgent()
    assert agent.llm is not None
    assert len(agent.tools) > 0
    assert agent.preferences == {'preferred_topics': [], 'watchlist_stocks': []}

@pytest.mark.asyncio
async def test_rephrase_news_item_brief(mock_llm):
    agent = NewsAgent()
    news_item = {'title': 'Test Title', 'summary': 'Test Summary.'}
    rephrased = await agent._rephrase_news_item(news_item, "brief")
    assert rephrased == "Rephrased summary"
    mock_llm.ainvoke.assert_called_once()
    assert "one-sentence brief" in mock_llm.ainvoke.call_args[0][0]

@pytest.mark.asyncio
async def test_rephrase_news_item_deep_dive(mock_llm):
    agent = NewsAgent()
    news_item = {'title': 'Test Title', 'summary': 'Test Summary.'}
    rephrased = await agent._rephrase_news_item(news_item, "deep_dive")
    assert rephrased == "Rephrased summary"
    mock_llm.ainvoke.assert_called_once()
    assert "3-4 sentences long" in mock_llm.ainvoke.call_args[0][0]

@pytest.mark.asyncio
async def test_process_fetched_news(mock_llm):
    agent = NewsAgent()
    raw_news = [
        {'title': 'News A', 'summary': 'Summary A.'},
        {'title': 'News B', 'summary': 'Summary B.'},
    ]
    
    # Mock _rephrase_news_item to return distinct values for brief and deep_dive
    mock_llm.ainvoke.side_effect = [
        MagicMock(content="Brief A"), # For brief A
        MagicMock(content="Brief B"), # For brief B
        MagicMock(content="Deep Dive A"), # For deep dive A
        MagicMock(content="Deep Dive B"), # For deep dive B
    ]

    response_text = await agent.process_fetched_news(raw_news)
    assert "Here are the latest news headlines:" in response_text
    assert "1. Brief A" in response_text
    assert "2. Brief B" in response_text
    assert agent.news_cache[0] == "Deep Dive A"
    assert agent.news_cache[1] == "Deep Dive B"
    assert agent.current_news_items == raw_news

@pytest.mark.asyncio
async def test_add_preferred_topic(mock_llm, mock_memory_functions):
    agent = NewsAgent()
    mock_load, mock_save = mock_memory_functions
    
    # Access the tool directly from the agent instance
    add_tool = next(t for t in agent.tools if t.name == "add_preferred_topic")
    
    result = add_tool.func("technology")
    assert "Added 'technology' to your preferred topics." in result
    assert "technology" in agent.preferred_topics
    mock_save.assert_called_once()

@pytest.mark.asyncio
async def test_get_preferred_topics(mock_llm, mock_memory_functions):
    agent = NewsAgent()
    agent.preferences = {'preferred_topics': ["tech", "finance"], 'watchlist_stocks': []}
    agent.preferred_topics = ["tech", "finance"]
    
    get_tool = next(t for t in agent.tools if t.name == "get_preferred_topics")
    
    result = get_tool.func()
    assert "Your preferred topics are: tech, finance." in result

@pytest.mark.asyncio
async def test_remove_preferred_topic(mock_llm, mock_memory_functions):
    agent = NewsAgent()
    agent.preferences = {'preferred_topics': ["tech", "finance"], 'watchlist_stocks': []}
    agent.preferred_topics = ["tech", "finance"]
    mock_load, mock_save = mock_memory_functions
    
    remove_tool = next(t for t in agent.tools if t.name == "remove_preferred_topic")
    
    result = remove_tool.func("tech")
    assert "Removed 'tech' from your preferred topics." in result
    assert "tech" not in agent.preferred_topics
    mock_save.assert_called_once()

@pytest.mark.asyncio
async def test_add_watchlist_stock(mock_llm, mock_memory_functions):
    agent = NewsAgent()
    mock_load, mock_save = mock_memory_functions
    
    add_tool = next(t for t in agent.tools if t.name == "add_watchlist_stock")
    
    result = add_tool.func("GOOG")
    assert "Added 'GOOG' to your watchlist." in result
    assert "GOOG" in agent.watchlist_stocks
    mock_save.assert_called_once()

@pytest.mark.asyncio
async def test_get_watchlist_stocks(mock_llm, mock_memory_functions):
    agent = NewsAgent()
    agent.preferences = {'preferred_topics': [], 'watchlist_stocks': ["AAPL", "MSFT"]}
    agent.watchlist_stocks = ["AAPL", "MSFT"]
    
    get_tool = next(t for t in agent.tools if t.name == "get_watchlist_stocks")
    
    result = get_tool.func()
    assert "Your watchlist stocks are: AAPL, MSFT." in result

@pytest.mark.asyncio
async def test_remove_watchlist_stock(mock_llm, mock_memory_functions):
    agent = NewsAgent()
    agent.preferences = {'preferred_topics': [], 'watchlist_stocks': ["AAPL", "MSFT"]}
    agent.watchlist_stocks = ["AAPL", "MSFT"]
    mock_load, mock_save = mock_memory_functions
    
    remove_tool = next(t for t in agent.tools if t.name == "remove_watchlist_stock")
    
    result = remove_tool.func("AAPL")
    assert "Removed 'AAPL' from your watchlist." in result
    assert "AAPL" not in agent.watchlist_stocks
    mock_save.assert_called_once()
