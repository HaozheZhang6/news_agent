"""Complete WebSocket manager with audio processing."""
import asyncio
import json
import uuid
import base64
from typing import Dict
from datetime import datetime
from fastapi import WebSocket
from starlette.websockets import WebSocketState


class AudioWebSocketManager:
    """WebSocket manager with full audio pipeline."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}
        # Will be injected by endpoint
        self.streaming_handler = None
        self.agent = None
        
    def set_handlers(self, streaming_handler, agent):
        """Set audio processing handlers."""
        self.streaming_handler = streaming_handler
        self.agent = agent
        
    def is_connected(self, session_id: str) -> bool:
        """Check if session has active WebSocket."""
        if session_id not in self.connections:
            return False
        ws = self.connections[session_id]
        return ws.client_state == WebSocketState.CONNECTED
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Register new WebSocket connection."""
        session_id = str(uuid.uuid4())
        self.connections[session_id] = websocket
        self.user_sessions[user_id] = session_id
        
        print(f"✅ [CONNECT] session={session_id[:8]}..., user={user_id[:8]}...")
        
        await self.send(session_id, {
            "event": "connected",
            "data": {
                "session_id": session_id,
                "message": "Ready for audio",
                "timestamp": datetime.now().isoformat()
            }
        })
        
        return session_id
    
    async def disconnect(self, session_id: str):
        """Remove WebSocket connection."""
        if session_id in self.connections:
            del self.connections[session_id]
            print(f"🔌 [DISCONNECT] session={session_id[:8]}...")
    
    async def send(self, session_id: str, message: dict):
        """Send message to WebSocket."""
        if not self.is_connected(session_id):
            print(f"⚠️  [SEND] Cannot send - not connected: {session_id[:8]}...")
            return
        
        try:
            websocket = self.connections[session_id]
            await websocket.send_text(json.dumps(message))
            event = message.get('event', 'unknown')
            print(f"📤 [SEND] {event} → session={session_id[:8]}...")
        except Exception as e:
            print(f"❌ [SEND ERROR] session={session_id[:8]}...: {e}")
            await self.disconnect(session_id)
    
    async def handle_audio_chunk(self, session_id: str, data: dict):
        """Process audio chunk through full pipeline."""
        try:
            print(f"🎤 [AUDIO IN] Processing chunk from session={session_id[:8]}...")
            
            # Get user ID
            user_id = "anonymous"
            for uid, sid in self.user_sessions.items():
                if sid == session_id:
                    user_id = uid
                    break
            
            # Decode audio
            audio_b64 = data.get("audio_chunk", "")
            if not audio_b64:
                print(f"❌ [AUDIO] No audio data in chunk")
                return
                
            audio_bytes = base64.b64decode(audio_b64)
            audio_format = data.get("format", "webm")
            print(f"📊 [AUDIO] Received {len(audio_bytes)} bytes, format={audio_format}")
            
            # Step 1: Transcribe audio
            print(f"🔄 [ASR] Starting transcription...")
            transcription = await self.streaming_handler.transcribe_chunk(
                audio_bytes, 
                format=audio_format
            )
            print(f"📝 [ASR] Transcribed: '{transcription}'")
            
            # Send transcription to frontend
            await self.send(session_id, {
                "event": "transcription",
                "data": {
                    "text": transcription,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Step 2: Get agent response
            print(f"🤖 [AGENT] Getting response...")
            response_result = await self.agent.process_voice_command(
                transcription, 
                user_id, 
                session_id
            )
            response_text = response_result.get("response_text", "I didn't understand that.")
            print(f"💬 [AGENT] Response: '{response_text[:50]}...'")
            
            # Send agent response text
            await self.send(session_id, {
                "event": "agent_response",
                "data": {
                    "text": response_text,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Step 3: Generate and stream TTS audio
            print(f"🔊 [TTS] Generating speech...")
            chunk_count = 0
            async for audio_chunk in self.streaming_handler.stream_tts_audio(response_text):
                await self.send(session_id, {
                    "event": "tts_chunk",
                    "data": {
                        "audio_chunk": base64.b64encode(audio_chunk).decode(),
                        "chunk_index": chunk_count,
                        "format": "mp3",
                        "timestamp": datetime.now().isoformat()
                    }
                })
                chunk_count += 1
            
            print(f"✅ [TTS] Sent {chunk_count} audio chunks")
            
            # Send completion event
            await self.send(session_id, {
                "event": "streaming_complete",
                "data": {
                    "total_chunks": chunk_count,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            print(f"🎉 [COMPLETE] Full audio pipeline finished for session={session_id[:8]}...")
            
        except Exception as e:
            print(f"❌ [AUDIO ERROR] session={session_id[:8]}...: {e}")
            import traceback
            traceback.print_exc()
            await self.send(session_id, {
                "event": "error",
                "data": {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            })
    
    async def handle_message(self, session_id: str, message: str):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            event = data.get("event")
            print(f"📥 [RECV] {event} from session={session_id[:8]}...")
            
            if event == "audio_chunk":
                await self.handle_audio_chunk(session_id, data.get("data", {}))
            elif event == "test":
                # Echo test messages
                await self.send(session_id, {
                    "event": "test_ack",
                    "data": {
                        "received": data.get("data"),
                        "timestamp": datetime.now().isoformat()
                    }
                })
            else:
                print(f"⚠️  [RECV] Unknown event: {event}")
                
        except Exception as e:
            print(f"❌ [MESSAGE ERROR]: {e}")
            import traceback
            traceback.print_exc()


# Global instance
_audio_ws_manager = AudioWebSocketManager()

def get_audio_ws_manager() -> AudioWebSocketManager:
    """Get audio WebSocket manager instance."""
    return _audio_ws_manager
