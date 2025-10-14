#!/bin/bash
# Test audio file upload via WebSocket using websocat

# Check if websocat is installed
if ! command -v websocat &> /dev/null; then
    echo "❌ websocat not found. Install with: brew install websocat"
    exit 1
fi

# Default values
URL="ws://localhost:8000/ws/voice"
AUDIO_FILE=""
USER_ID="03f6b167-0c4d-4983-a380-54b8eb42f830"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --render)
            URL="wss://voice-news-agent-api.onrender.com/ws/voice"
            shift
            ;;
        --url)
            URL="$2"
            shift 2
            ;;
        --audio)
            AUDIO_FILE="$2"
            shift 2
            ;;
        --user-id)
            USER_ID="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --render          Use deployed backend on Render"
            echo "  --url URL         Custom WebSocket URL"
            echo "  --audio FILE      Audio file to send"
            echo "  --user-id ID      User ID (default: demo user)"
            echo "  -h, --help        Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🔌 Connecting to: $URL"
echo "👤 User ID: $USER_ID"

if [ -n "$AUDIO_FILE" ]; then
    if [ ! -f "$AUDIO_FILE" ]; then
        echo "❌ Audio file not found: $AUDIO_FILE"
        exit 1
    fi
    
    echo "🎵 Audio file: $AUDIO_FILE"
    
    # Convert audio to base64
    AUDIO_B64=$(base64 -i "$AUDIO_FILE")
    
    # Determine format
    EXT="${AUDIO_FILE##*.}"
    case "$EXT" in
        wav|wave) FORMAT="wav" ;;
        mp3) FORMAT="mp3" ;;
        webm) FORMAT="webm" ;;
        ogg) FORMAT="ogg" ;;
        *) FORMAT="wav" ;;
    esac
    
    echo "🎵 Format: $FORMAT"
    
    # Create JSON message
    SESSION_ID=$(uuidgen)
    MESSAGE=$(cat <<EOF
{
  "event": "audio_chunk",
  "data": {
    "audio_chunk": "$AUDIO_B64",
    "format": "$FORMAT",
    "is_final": true,
    "session_id": "$SESSION_ID",
    "user_id": "$USER_ID"
  }
}
EOF
)
    
    echo "📤 Sending audio via WebSocket..."
    echo "$MESSAGE" | websocat "$URL"
    
else
    echo "📝 No audio file provided, sending text command..."
    
    SESSION_ID=$(uuidgen)
    MESSAGE=$(cat <<EOF
{
  "event": "voice_command",
  "data": {
    "command": "tell me the news",
    "user_id": "$USER_ID",
    "session_id": "$SESSION_ID"
  }
}
EOF
)
    
    echo "📤 Sending text command via WebSocket..."
    echo "$MESSAGE" | websocat "$URL"
fi
