"""FastAPI main application for Voice News Agent Backend."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import get_settings
from .database import get_database
from .cache import get_cache
from .core.websocket_manager import get_websocket_manager
from .api import voice, news, conversation, user
from .api.profile import router as profile_router
from .api.conversation_log import router as conversation_log_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting Voice News Agent Backend...")
    
    try:
        # Initialize database
        db = await get_database()
        await db.initialize()
        print("✅ Database initialized")
        
        # Initialize cache
        cache = await get_cache()
        await cache.initialize()
        print("✅ Cache initialized")
        
        # Initialize WebSocket manager
        ws_manager = await get_websocket_manager()
        print("✅ WebSocket manager initialized")
        
        print("🎉 Backend startup complete!")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Voice News Agent Backend...")
    print("✅ Backend shutdown complete!")


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

# Include API routers
app.include_router(voice.router)
app.include_router(news.router)
app.include_router(conversation.router)
app.include_router(user.router)
app.include_router(profile_router)
app.include_router(conversation_log_router)


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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database
        db = await get_database()
        db_healthy = await db.health_check()
        
        # Check cache
        cache = await get_cache()
        cache_healthy = await cache.health_check()
        
        # Check WebSocket manager
        ws_manager = await get_websocket_manager()
        ws_healthy = ws_manager.get_active_connections_count() >= 0
        
        overall_healthy = db_healthy and cache_healthy and ws_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "services": {
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
                "websocket": "healthy" if ws_healthy else "unhealthy"
            },
            "active_connections": ws_manager.get_active_connections_count(),
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
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
    try:
        # Get WebSocket manager
        ws_manager = await get_websocket_manager()
        
        # Extract user ID from query parameters or headers
        # In a real implementation, you would authenticate the user
        user_id = websocket.query_params.get("user_id", "anonymous")
        
        # Connect WebSocket
        session_id = await ws_manager.connect(websocket, user_id)
        
        # Handle messages
        while True:
            try:
                message = await websocket.receive_text()
                await ws_manager.process_message(websocket, message)
                
            except WebSocketDisconnect:
                print(f"WebSocket disconnected: {session_id}")
                await ws_manager.disconnect(session_id)
                break
                
            except Exception as e:
                print(f"Error processing WebSocket message: {e}")
                await ws_manager.send_message(session_id, {
                    "event": "error",
                    "data": {
                        "error_type": "message_processing_failed",
                        "message": str(e),
                        "session_id": session_id
                    }
                })
                
    except WebSocketDisconnect:
        print("WebSocket disconnected")
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
