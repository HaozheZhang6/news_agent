"""Stock-related Pydantic models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class StockData(BaseModel):
    """Stock data model."""
    id: str = Field(..., description="Stock data ID")
    symbol: str = Field(..., description="Stock symbol")
    company_name: Optional[str] = Field(None, description="Company name")
    current_price: Optional[float] = Field(None, description="Current price")
    change_percent: Optional[float] = Field(None, description="Change percentage")
    volume: Optional[int] = Field(None, description="Trading volume")
    market_cap: Optional[int] = Field(None, description="Market capitalization")
    last_updated: datetime = Field(..., description="Last update timestamp")


class StockQuote(BaseModel):
    """Stock quote model."""
    symbol: str = Field(..., description="Stock symbol")
    price: float = Field(..., description="Current price")
    change: float = Field(..., description="Price change")
    change_percent: float = Field(..., description="Change percentage")
    volume: int = Field(..., description="Trading volume")
    market_cap: Optional[int] = Field(None, description="Market capitalization")
    high_52_week: Optional[float] = Field(None, description="52-week high")
    low_52_week: Optional[float] = Field(None, description="52-week low")
    pe_ratio: Optional[float] = Field(None, description="P/E ratio")
    dividend_yield: Optional[float] = Field(None, description="Dividend yield")
    last_updated: datetime = Field(..., description="Last update timestamp")


class StockWatchlist(BaseModel):
    """Stock watchlist model."""
    user_id: str = Field(..., description="User ID")
    symbols: List[str] = Field(..., description="Stock symbols")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class StockWatchlistUpdate(BaseModel):
    """Stock watchlist update model."""
    symbols: List[str] = Field(..., description="Stock symbols")


class StockAnalysis(BaseModel):
    """Stock analysis model."""
    symbol: str = Field(..., description="Stock symbol")
    analysis_type: str = Field(..., description="Analysis type")
    summary: str = Field(..., description="Analysis summary")
    key_metrics: Dict[str, Any] = Field(..., description="Key metrics")
    recommendations: List[str] = Field(..., description="Recommendations")
    confidence_score: float = Field(..., description="Confidence score")
    analysis_date: datetime = Field(..., description="Analysis date")
    expires_at: datetime = Field(..., description="Analysis expiration")


class StockNews(BaseModel):
    """Stock-related news model."""
    symbol: str = Field(..., description="Stock symbol")
    news_items: List[Dict[str, Any]] = Field(..., description="Related news items")
    sentiment_score: float = Field(..., description="Overall sentiment score")
    news_count: int = Field(..., description="News count")
    last_updated: datetime = Field(..., description="Last update timestamp")


class StockAlert(BaseModel):
    """Stock alert model."""
    id: str = Field(..., description="Alert ID")
    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Stock symbol")
    alert_type: str = Field(..., description="Alert type (price_change/volume_spike/news)")
    threshold_value: float = Field(..., description="Threshold value")
    current_value: float = Field(..., description="Current value")
    message: str = Field(..., description="Alert message")
    is_triggered: bool = Field(default=False, description="Alert triggered status")
    created_at: datetime = Field(..., description="Alert creation timestamp")
    triggered_at: Optional[datetime] = Field(None, description="Alert trigger timestamp")


class StockAlertCreate(BaseModel):
    """Stock alert creation model."""
    symbol: str = Field(..., description="Stock symbol")
    alert_type: str = Field(..., description="Alert type")
    threshold_value: float = Field(..., description="Threshold value")
    message: Optional[str] = Field(None, description="Custom alert message")


class MarketSummary(BaseModel):
    """Market summary model."""
    market_status: str = Field(..., description="Market status")
    market_cap: float = Field(..., description="Total market capitalization")
    volume: int = Field(..., description="Total volume")
    advancing_stocks: int = Field(..., description="Advancing stocks count")
    declining_stocks: int = Field(..., description="Declining stocks count")
    unchanged_stocks: int = Field(..., description="Unchanged stocks count")
    top_gainers: List[Dict[str, Any]] = Field(..., description="Top gaining stocks")
    top_losers: List[Dict[str, Any]] = Field(..., description="Top losing stocks")
    most_active: List[Dict[str, Any]] = Field(..., description="Most active stocks")
    last_updated: datetime = Field(..., description="Last update timestamp")


class StockRequest(BaseModel):
    """Stock request model."""
    symbols: List[str] = Field(..., description="Stock symbols")
    include_news: bool = Field(default=False, description="Include related news")
    include_analysis: bool = Field(default=False, description="Include analysis")
    include_alerts: bool = Field(default=False, description="Include alerts")


class StockResponse(BaseModel):
    """Stock response model."""
    quotes: List[StockQuote] = Field(..., description="Stock quotes")
    news: Optional[Dict[str, List[Dict[str, Any]]]] = Field(None, description="Stock news")
    analysis: Optional[Dict[str, StockAnalysis]] = Field(None, description="Stock analysis")
    alerts: Optional[List[StockAlert]] = Field(None, description="Stock alerts")
    market_summary: Optional[MarketSummary] = Field(None, description="Market summary")
    processing_time_ms: int = Field(..., description="Processing time")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class StockSearchRequest(BaseModel):
    """Stock search request model."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum results")
    include_etfs: bool = Field(default=True, description="Include ETFs")
    include_crypto: bool = Field(default=False, description="Include cryptocurrencies")


class StockSearchResult(BaseModel):
    """Stock search result model."""
    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    exchange: str = Field(..., description="Exchange")
    sector: Optional[str] = Field(None, description="Sector")
    industry: Optional[str] = Field(None, description="Industry")
    market_cap: Optional[int] = Field(None, description="Market capitalization")
    current_price: Optional[float] = Field(None, description="Current price")
    change_percent: Optional[float] = Field(None, description="Change percentage")
    relevance_score: float = Field(..., description="Relevance score")
