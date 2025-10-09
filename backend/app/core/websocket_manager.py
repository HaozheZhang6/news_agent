"""WebSocket manager for real-time voice communication."""
import asyncio
import json
import uuid
from typing import Dict, Any, Optional, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from app.core.agent_wrapper import get_agent
from app.database import get_database
from app.cache import get_cache


class WebSocketManager:
    """Manages WebSocket connections for voice communication."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.session_data: Dict[str, Dict[str, Any]] = {}  # session_id -> data
        self._initialized = False
    
    async def initialize(self):
        """Initialize the WebSocket manager."""
        if self._initialized:
            return
        
        self.db = await get_database()
        self.cache = await get_cache()
        self.agent = await get_agent()
        self._initialized = True
        print("✅ WebSocketManager initialized successfully")
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Accept WebSocket connection and create session."""
        try:
            if not self._initialized:
                await self.initialize()
            
            await websocket.accept()
            
            # Create new session
            session_id = str(uuid.uuid4())
            session_data = {
                "user_id": user_id,
                "websocket": websocket,
                "session_start": datetime.now(),
                "total_commands": 0,
                "total_interruptions": 0,
                "is_active": True
            }
            
            # Store connections
            self.active_connections[session_id] = websocket
            self.user_sessions[user_id] = session_id
            self.session_data[session_id] = session_data
            
            # Create session in database
            await self.db.create_conversation_session(user_id)
            
            print(f"✅ WebSocket connected: {session_id} for user {user_id}")
            
            # Send welcome message
            await self.send_message(session_id, {
                "event": "connected",
                "data": {
                    "session_id": session_id,
                    "message": "Connected to Voice News Agent",
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            return session_id
            
        except Exception as e:
            print(f"❌ Error connecting WebSocket: {e}")
            raise
    
    async def disconnect(self, session_id: str):
        """Handle WebSocket disconnection."""
        try:
            if session_id in self.active_connections:
                # Update session end time
                if session_id in self.session_data:
                    self.session_data[session_id]["session_end"] = datetime.now()
                    self.session_data[session_id]["is_active"] = False
                
                # Remove from active connections
                websocket = self.active_connections.pop(session_id)
                
                # Remove user session mapping
                user_id = self.session_data.get(session_id, {}).get("user_id")
                if user_id and user_id in self.user_sessions:
                    del self.user_sessions[user_id]
                
                # Clean up session data
                if session_id in self.session_data:
                    del self.session_data[session_id]
                
                print(f"✅ WebSocket disconnected: {session_id}")
                
        except Exception as e:
            print(f"❌ Error disconnecting WebSocket: {e}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send message to specific WebSocket connection."""
        try:
            if session_id in self.active_connections:
                websocket = self.active_connections[session_id]
                await websocket.send_text(json.dumps(message))
            else:
                print(f"⚠️ WebSocket {session_id} not found")
                
        except Exception as e:
            print(f"❌ Error sending message to {session_id}: {e}")
            # Remove disconnected connection
            await self.disconnect(session_id)
    
    async def broadcast_message(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """Broadcast message to all active connections."""
        exclude = exclude or set()
        
        for session_id in list(self.active_connections.keys()):
            if session_id not in exclude:
                await self.send_message(session_id, message)
    
    async def handle_voice_command(self, session_id: str, data: Dict[str, Any]):
        """Handle voice command from client."""
        try:
            if not self._initialized:
                await self.initialize()
            
            command = data.get("command", "")
            user_id = self.session_data.get(session_id, {}).get("user_id")
            
            if not user_id:
                await self.send_message(session_id, {
                    "event": "error",
                    "data": {
                        "error_type": "invalid_session",
                        "message": "Invalid session",
                        "session_id": session_id
                    }
                })
                return
            
            # Update session stats
            if session_id in self.session_data:
                self.session_data[session_id]["total_commands"] += 1
            
            # Send transcription confirmation
            await self.send_message(session_id, {
                "event": "transcription",
                "data": {
                    "text": command,
                    "confidence": data.get("confidence", 0.95),
                    "session_id": session_id,
                    "processing_time_ms": 150
                }
            })
            
            # Process command through agent
            start_time = datetime.now()
            result = await self.agent.process_voice_command(command, user_id, session_id)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Send response
            await self.send_message(session_id, {
                "event": "voice_response",
                "data": {
                    "text": result["response_text"],
                    "audio_url": result.get("audio_url"),
                    "response_type": result["response_type"],
                    "processing_time_ms": int(processing_time),
                    "session_id": session_id,
                    "news_items": result.get("news_items", []),
                    "stock_data": result.get("stock_data"),
                    "timestamp": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            print(f"❌ Error handling voice command: {e}")
            await self.send_message(session_id, {
                "event": "error",
                "data": {
                    "error_type": "command_processing_failed",
                    "message": str(e),
                    "session_id": session_id
                }
            })
    
    async def handle_voice_data(self, session_id: str, data: Dict[str, Any]):
        """Handle voice audio data from client."""
        try:
            if not self._initialized:
                await self.initialize()
            
            audio_chunk = data.get("audio_chunk", "")
            user_id = self.session_data.get(session_id, {}).get("user_id")
            
            if not user_id:
                await self.send_message(session_id, {
                    "event": "error",
                    "data": {
                        "error_type": "invalid_session",
                        "message": "Invalid session",
                        "session_id": session_id
                    }
                })
                return
            
            # For now, just acknowledge receipt
            # In a full implementation, you would process the audio chunk
            await self.send_message(session_id, {
                "event": "audio_received",
                "data": {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            print(f"❌ Error handling voice data: {e}")
            await self.send_message(session_id, {
                "event": "error",
                "data": {
                    "error_type": "audio_processing_failed",
                    "message": str(e),
                    "session_id": session_id
                }
            })
    
    async def handle_interrupt(self, session_id: str, data: Dict[str, Any]):
        """Handle voice interruption."""
        try:
            if session_id in self.session_data:
                self.session_data[session_id]["total_interruptions"] += 1
            
            # Send interruption confirmation
            await self.send_message(session_id, {
                "event": "voice_interrupted",
                "data": {
                    "session_id": session_id,
                    "reason": data.get("reason", "user_interruption"),
                    "interruption_time_ms": 85,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            print(f"❌ Error handling interrupt: {e}")
    
    async def handle_start_listening(self, session_id: str, data: Dict[str, Any]):
        """Handle start listening command."""
        try:
            await self.send_message(session_id, {
                "event": "listening_started",
                "data": {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            print(f"❌ Error handling start listening: {e}")
    
    async def handle_stop_listening(self, session_id: str, data: Dict[str, Any]):
        """Handle stop listening command."""
        try:
            await self.send_message(session_id, {
                "event": "listening_stopped",
                "data": {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            print(f"❌ Error handling stop listening: {e}")
    
    async def process_message(self, websocket: WebSocket, message: str):
        """Process incoming WebSocket message."""
        try:
            data = json.loads(message)
            event = data.get("event")
            session_id = data.get("data", {}).get("session_id")
            
            if not session_id:
                print("⚠️ No session_id in message")
                return
            
            # Route message to appropriate handler
            if event == "voice_command":
                await self.handle_voice_command(session_id, data.get("data", {}))
            elif event == "voice_data":
                await self.handle_voice_data(session_id, data.get("data", {}))
            elif event == "interrupt":
                await self.handle_interrupt(session_id, data.get("data", {}))
            elif event == "start_listening":
                await self.handle_start_listening(session_id, data.get("data", {}))
            elif event == "stop_listening":
                await self.handle_stop_listening(session_id, data.get("data", {}))
            else:
                print(f"⚠️ Unknown event: {event}")
                
        except json.JSONDecodeError:
            print("❌ Invalid JSON in WebSocket message")
        except Exception as e:
            print(f"❌ Error processing WebSocket message: {e}")
    
    def get_active_connections_count(self) -> int:
        """Get count of active connections."""
        return len(self.active_connections)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        return self.session_data.get(session_id)
    
    def get_user_session(self, user_id: str) -> Optional[str]:
        """Get session ID for user."""
        return self.user_sessions.get(user_id)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager instance."""
    if not websocket_manager._initialized:
        await websocket_manager.initialize()
    return websocket_manager
