"""News-related Pydantic models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class NewsSource(BaseModel):
    """News source model."""
    id: str = Field(..., description="Source ID")
    name: str = Field(..., description="Source name")
    url: Optional[str] = Field(None, description="Source URL")
    category: str = Field(..., description="Source category")
    reliability_score: float = Field(..., description="Reliability score (0-1)")
    is_active: bool = Field(default=True, description="Source active status")
    created_at: datetime = Field(..., description="Creation timestamp")


class NewsArticle(BaseModel):
    """News article model."""
    id: str = Field(..., description="Article ID")
    source_id: str = Field(..., description="Source ID")
    external_id: Optional[str] = Field(None, description="External source ID")
    title: str = Field(..., description="Article title")
    summary: Optional[str] = Field(None, description="Article summary")
    content: Optional[str] = Field(None, description="Article content")
    url: Optional[str] = Field(None, description="Article URL")
    published_at: datetime = Field(..., description="Publication timestamp")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score (-1 to 1)")
    relevance_score: float = Field(default=0.5, description="Relevance score (0-1)")
    topics: List[str] = Field(default=[], description="Article topics")
    keywords: List[str] = Field(default=[], description="Article keywords")
    is_breaking: bool = Field(default=False, description="Breaking news flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    source: Optional[NewsSource] = Field(None, description="News source")


class NewsArticleCreate(BaseModel):
    """News article creation model."""
    source_id: str = Field(..., description="Source ID")
    external_id: Optional[str] = Field(None, description="External source ID")
    title: str = Field(..., description="Article title")
    summary: Optional[str] = Field(None, description="Article summary")
    content: Optional[str] = Field(None, description="Article content")
    url: Optional[str] = Field(None, description="Article URL")
    published_at: datetime = Field(..., description="Publication timestamp")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score (-1 to 1)")
    relevance_score: float = Field(default=0.5, description="Relevance score (0-1)")
    topics: List[str] = Field(default=[], description="Article topics")
    keywords: List[str] = Field(default=[], description="Article keywords")
    is_breaking: bool = Field(default=False, description="Breaking news flag")


class NewsSearchRequest(BaseModel):
    """News search request model."""
    query: str = Field(..., description="Search query")
    category: Optional[str] = Field(None, description="News category filter")
    topics: Optional[List[str]] = Field(None, description="Topic filters")
    limit: int = Field(default=10, description="Maximum results")
    offset: int = Field(default=0, description="Results offset")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    sentiment_min: Optional[float] = Field(None, description="Minimum sentiment score")
    sentiment_max: Optional[float] = Field(None, description="Maximum sentiment score")


class NewsLatestRequest(BaseModel):
    """Latest news request model."""
    topics: Optional[List[str]] = Field(None, description="Topic filters")
    limit: int = Field(default=10, description="Maximum results")
    breaking_only: bool = Field(default=False, description="Breaking news only")
    category: Optional[str] = Field(None, description="Category filter")


class NewsSummaryRequest(BaseModel):
    """News summary request model."""
    article_ids: List[str] = Field(..., description="Article IDs to summarize")
    summary_type: str = Field(default="brief", description="Summary type (brief/deep_dive)")
    max_length: int = Field(default=200, description="Maximum summary length")


class NewsSummaryResponse(BaseModel):
    """News summary response model."""
    article_id: str = Field(..., description="Article ID")
    summary: str = Field(..., description="Generated summary")
    summary_type: str = Field(..., description="Summary type")
    word_count: int = Field(..., description="Summary word count")
    processing_time_ms: int = Field(..., description="Processing time")


class NewsResponse(BaseModel):
    """News response model."""
    articles: List[NewsArticle] = Field(..., description="News articles")
    total_count: int = Field(..., description="Total article count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    has_more: bool = Field(..., description="Has more pages")


class BreakingNewsAlert(BaseModel):
    """Breaking news alert model."""
    id: str = Field(..., description="Alert ID")
    article_id: str = Field(..., description="Article ID")
    title: str = Field(..., description="Alert title")
    summary: str = Field(..., description="Alert summary")
    severity: str = Field(..., description="Alert severity (low/medium/high)")
    topics: List[str] = Field(..., description="Alert topics")
    created_at: datetime = Field(..., description="Alert timestamp")
    expires_at: datetime = Field(..., description="Alert expiration")


class NewsTrend(BaseModel):
    """News trend model."""
    topic: str = Field(..., description="Trending topic")
    article_count: int = Field(..., description="Article count")
    sentiment_avg: float = Field(..., description="Average sentiment")
    trend_score: float = Field(..., description="Trend score")
    period: str = Field(..., description="Time period")
    created_at: datetime = Field(..., description="Trend timestamp")
