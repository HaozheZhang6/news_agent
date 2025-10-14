"""FastAPI main application for Voice News Agent Backend."""
import logging
from logging.handlers import RotatingFileHandler
import os
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import get_settings
from .database import get_database
from .cache import get_cache
from .core.websocket_manager import get_websocket_manager
from .api import voice, news, conversation, user
from .api.profile import router as profile_router
from .api.conversation_log import router as conversation_log_router
from .api import websocket_simple
from .api.conversation_session import router as conversation_session_router
from .utils.logger import get_logger
from .utils.conversation_logger import get_conversation_logger

settings = get_settings()
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with non-blocking startup."""
    # Startup
    # Setup logging to file and console
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("voice_news_agent")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = RotatingFileHandler("logs/app.log", maxBytes=2_000_000, backupCount=3)
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    logger.info("🚀 Starting Voice News Agent Backend...")
    
    # Initialize services with timeouts and graceful degradation
    async def initialize_services():
        """Initialize services with timeouts."""
        try:
            # Check configuration first
            if not settings.is_database_configured():
                logger.warning("⚠️ Database not configured - skipping DB initialization")
            else:
                # Initialize database with timeout
                try:
                    db = await asyncio.wait_for(get_database(), timeout=10.0)
                    await asyncio.wait_for(db.initialize(), timeout=10.0)
                    logger.info("✅ Database initialized")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Database initialization timed out - continuing without DB")
                except Exception as e:
                    logger.warning(f"⚠️ Database initialization failed: {e} - continuing without DB")
            
            if not settings.is_cache_configured():
                logger.warning("⚠️ Cache not configured - skipping cache initialization")
            else:
                # Initialize cache with timeout
                try:
                    cache = await asyncio.wait_for(get_cache(), timeout=10.0)
                    await asyncio.wait_for(cache.initialize(), timeout=10.0)
                    logger.info("✅ Cache initialized")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Cache initialization timed out - continuing without cache")
                except Exception as e:
                    logger.warning(f"⚠️ Cache initialization failed: {e} - continuing without cache")
            
            # Initialize WebSocket manager (this should be fast)
            try:
                ws_manager = await get_websocket_manager()
                logger.info("✅ WebSocket manager initialized")
            except Exception as e:
                logger.warning(f"⚠️ WebSocket manager initialization failed: {e}")
            
            logger.info("🎉 Backend startup complete!")
            
        except Exception as e:
            logger.error(f"❌ Critical startup error: {e}")
            # Don't raise - let the app start anyway
    
    # Start initialization in background - don't block the app startup
    asyncio.create_task(initialize_services())
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Voice News Agent Backend...")
    logger.info("✅ Backend shutdown complete!")


# Create FastAPI application
app = FastAPI(
    title="Voice News Agent API",
    description="AI-powered voice-activated news assistant with real-time interruption",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses."""
    start_time = time.time()
    
    # Log request
    logger.info(f"📥 HTTP | {request.method} {request.url.path} | client={request.client.host if request.client else 'unknown'}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Log response
    logger.info(f"📤 HTTP | {request.method} {request.url.path} | status={response.status_code} | duration={duration_ms}ms")
    
    return response

# Include API routers
app.include_router(voice.router)
app.include_router(news.router)
app.include_router(conversation.router)
app.include_router(user.router)
app.include_router(profile_router)
app.include_router(conversation_log_router)
app.include_router(websocket_simple.router)
app.include_router(conversation_session_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Voice News Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "websocket": "/ws/voice"
    }


@app.get("/live")
async def live_check():
    """Ultra-lightweight liveness check for Render port scanning."""
    return {"status": "alive"}


@app.get("/health")
async def health_check():
    """Lightweight health check endpoint for Render port scanning."""
    return {"status": "ok", "message": "Voice News Agent API is running"}


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check endpoint with service status."""
    try:
        # Check database with timeout
        db_healthy = False
        try:
            db = await get_database()
            db_healthy = await asyncio.wait_for(db.health_check(), timeout=5.0)
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
        
        # Check cache with timeout
        cache_healthy = False
        try:
            cache = await get_cache()
            cache_healthy = await asyncio.wait_for(cache.health_check(), timeout=5.0)
        except Exception as e:
            logger.warning(f"Cache health check failed: {e}")
        
        # Check WebSocket manager
        ws_healthy = False
        try:
            ws_manager = await get_websocket_manager()
            ws_healthy = ws_manager.get_active_connections_count() >= 0
        except Exception as e:
            logger.warning(f"WebSocket health check failed: {e}")
        
        overall_healthy = db_healthy and cache_healthy and ws_healthy
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "services": {
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
                "websocket": "healthy" if ws_healthy else "unhealthy"
            },
            "active_connections": ws_manager.get_active_connections_count() if ws_healthy else 0,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )


@app.websocket("/ws/voice")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time voice communication."""
    session_id = None
    try:
        # Get WebSocket manager
        ws_manager = await get_websocket_manager()

        # Accept early to avoid "need to call accept first" when sending initial errors
        await websocket.accept()

        # Extract user ID from query parameters or headers
        # Use default UUID for anonymous users (Supabase requires valid UUID)
        user_id = websocket.query_params.get("user_id", "00000000-0000-0000-0000-000000000000")

        # Connect WebSocket (this will register the connection and send 'connected')
        session_id = await ws_manager.connect(websocket, user_id)

        # Handle messages
        while True:
            try:
                message = await websocket.receive_text()
                await ws_manager.process_message(websocket, message)

            except WebSocketDisconnect:
                print(f"WebSocket disconnected: {session_id}")
                if session_id:
                    await ws_manager.disconnect(session_id)
                break

            except Exception as e:
                print(f"Error processing WebSocket message: {e}")
                if session_id:
                    await ws_manager.send_message(session_id, {
                        "event": "error",
                        "data": {
                            "error_type": "message_processing_failed",
                            "message": str(e),
                            "session_id": session_id
                        }
                    })
                # On unexpected error, break to avoid repeated receive loop errors
                break

    except Exception as e:
        print(f"WebSocket error: {e}")


@app.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status."""
    try:
        ws_manager = await get_websocket_manager()
        
        return {
            "active_connections": ws_manager.get_active_connections_count(),
            "max_connections": settings.max_websocket_connections,
            "status": "running"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1
    )
