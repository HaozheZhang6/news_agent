"""WebSocket endpoint with full audio pipeline."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.websocket_manager_v2 import get_audio_ws_manager
from ..core.streaming_handler import get_streaming_handler
from ..core.agent_wrapper import get_agent

router = APIRouter()


@router.websocket("/ws/voice/simple")
async def websocket_audio_endpoint(websocket: WebSocket):
    """WebSocket endpoint with complete audio processing."""
    session_id = None
    
    try:
        # Step 1: Accept connection
        await websocket.accept()
        print("✅ [ACCEPT] WebSocket connection accepted")
        
        # Step 2: Get dependencies
        manager = get_audio_ws_manager()
        streaming_handler = get_streaming_handler()
        agent = await get_agent()
        
        # Inject handlers into manager
        manager.set_handlers(streaming_handler, agent)
        print("✅ [SETUP] Handlers injected into manager")
        
        # Step 3: Get user ID
        user_id = websocket.query_params.get("user_id", "anonymous")
        
        # Step 4: Register connection
        session_id = await manager.connect(websocket, user_id)
        print(f"✅ [REGISTER] Connection registered: {session_id[:8]}...")
        
        # Step 5: Message loop
        print(f"🔄 [LOOP] Starting message loop for session={session_id[:8]}...")
        while True:
            try:
                message = await websocket.receive_text()
                await manager.handle_message(session_id, message)
                
            except WebSocketDisconnect:
                print(f"🔌 [DISCONNECT] Client closed connection: {session_id[:8]}...")
                break
            except Exception as e:
                print(f"❌ [LOOP ERROR] session={session_id[:8]}...: {e}")
                break
    
    except Exception as e:
        print(f"❌ [ENDPOINT ERROR]: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if session_id:
            await manager.disconnect(session_id)
            print(f"🧹 [CLEANUP] Session cleaned up: {session_id[:8]}...")


@router.get("/ws/status/audio")
async def websocket_audio_status():
    """Get audio WebSocket status."""
    manager = get_audio_ws_manager()
    return {
        "active_connections": len(manager.connections),
        "status": "running",
        "endpoint": "/ws/voice/simple"
    }
