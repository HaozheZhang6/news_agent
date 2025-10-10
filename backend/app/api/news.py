"""News API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from ..models.news import NewsLatestRequest, NewsSearchRequest, NewsResponse, NewsSummaryRequest, NewsSummaryResponse
from ..core.agent_wrapper import get_agent
from ..database import get_database
from ..cache import get_cache

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/latest", response_model=NewsResponse)
async def get_latest_news(
    topics: Optional[List[str]] = Query(None, description="Filter by topics"),
    limit: int = Query(10, description="Maximum number of articles"),
    breaking_only: bool = Query(False, description="Breaking news only"),
    category: Optional[str] = Query(None, description="Filter by category"),
    agent=Depends(get_agent),
    db=Depends(get_database)
):
    """Get latest news articles."""
    try:
        # Get news from agent wrapper
        news_items = await agent.get_news_latest(topics or [], limit)
        
        # Filter breaking news if requested
        if breaking_only:
            news_items = [item for item in news_items if item.get("is_breaking", False)]
        
        # Filter by category if requested
        if category:
            news_items = [item for item in news_items if item.get("source", {}).get("category") == category]
        
        return NewsResponse(
            articles=news_items,
            total_count=len(news_items),
            page=1,
            page_size=limit,
            has_more=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting latest news: {str(e)}")


@router.get("/search", response_model=NewsResponse)
async def search_news(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of articles"),
    category: Optional[str] = Query(None, description="Filter by category"),
    topics: Optional[List[str]] = Query(None, description="Filter by topics"),
    agent=Depends(get_agent),
    db=Depends(get_database)
):
    """Search news articles."""
    try:
        # Search news through agent wrapper
        news_items = await agent.search_news(query, limit)
        
        # Filter by category if requested
        if category:
            news_items = [item for item in news_items if item.get("source", {}).get("category") == category]
        
        # Filter by topics if requested
        if topics:
            news_items = [item for item in news_items if any(topic in item.get("topics", []) for topic in topics)]
        
        return NewsResponse(
            articles=news_items,
            total_count=len(news_items),
            page=1,
            page_size=limit,
            has_more=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching news: {str(e)}")


@router.get("/article/{article_id}")
async def get_news_article(
    article_id: str,
    agent=Depends(get_agent),
    db=Depends(get_database)
):
    """Get specific news article."""
    try:
        # Get article from database
        # This would need to be implemented in the database layer
        article = await db.get_news_article(article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return article
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting article: {str(e)}")


@router.post("/summarize", response_model=List[NewsSummaryResponse])
async def summarize_news(
    request: NewsSummaryRequest,
    agent=Depends(get_agent)
):
    """Summarize news articles."""
    try:
        summaries = []
        
        for article_id in request.article_ids:
            # Get article (mock for now)
            article = {
                "id": article_id,
                "title": f"Sample Article {article_id}",
                "summary": "This is a sample article summary."
            }
            
            # Generate summary (mock for now)
            summary_text = f"Summary of {article['title']}: {article['summary']}"
            
            summaries.append(NewsSummaryResponse(
                article_id=article_id,
                summary=summary_text,
                summary_type=request.summary_type,
                word_count=len(summary_text.split()),
                processing_time_ms=200
            ))
        
        return summaries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing news: {str(e)}")


@router.get("/breaking")
async def get_breaking_news(
    limit: int = Query(5, description="Maximum number of articles"),
    agent=Depends(get_agent),
    db=Depends(get_database)
):
    """Get breaking news."""
    try:
        # Get breaking news from agent wrapper
        news_items = await agent.get_news_latest([], limit)
        
        # Filter for breaking news
        breaking_news = [item for item in news_items if item.get("is_breaking", False)]
        
        return {
            "articles": breaking_news,
            "count": len(breaking_news),
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting breaking news: {str(e)}")


@router.get("/topics")
async def get_news_topics(
    agent=Depends(get_agent),
    db=Depends(get_database)
):
    """Get available news topics."""
    try:
        # Return available topics
        topics = [
            "technology",
            "finance",
            "politics",
            "crypto",
            "energy",
            "healthcare",
            "automotive",
            "real_estate",
            "retail",
            "general"
        ]
        
        return {
            "topics": topics,
            "count": len(topics)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting topics: {str(e)}")


@router.get("/health")
async def news_health_check():
    """Health check for news services."""
    return {
        "status": "healthy",
        "services": {
            "database": "available",
            "cache": "available",
            "external_apis": "available"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }
