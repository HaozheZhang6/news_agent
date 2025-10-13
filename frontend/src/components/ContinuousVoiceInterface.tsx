import { useState, useEffect, useRef, useCallback } from "react";
import { Mic, MicOff, Volume2, VolumeX } from "lucide-react";
import { cn } from "./ui/utils";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { logger } from "../utils/logger";
import { useAudioEncoder } from "../utils/audio-encoder";

type VoiceState = "idle" | "listening" | "speaking" | "connecting";

interface ContinuousVoiceInterfaceProps {
  userId: string;
  onTranscription?: (text: string) => void;
  onResponse?: (text: string) => void;
  onError?: (error: string) => void;
}

/**
 * Continuous Voice Interface with VAD (Voice Activity Detection)
 * 
 * Key Features (mirroring src.main):
 * 1. Voice Activity Detection: Detects when user starts/stops talking
 * 2. Auto-send after silence: Sends audio 1 second after user stops talking
 * 3. Real-time interruption: Stops agent audio when user starts talking
 * 4. Continuous listening: Always listening when active
 */
export function ContinuousVoiceInterface({ 
  userId, 
  onTranscription, 
  onResponse, 
  onError 
}: ContinuousVoiceInterfaceProps) {
  // Audio encoder hook
  const audioEncoder = useAudioEncoder(userId);
  
  // State management
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [isConnected, setIsConnected] = useState(false);
  const [currentTranscription, setCurrentTranscription] = useState("");
  const [currentResponse, setCurrentResponse] = useState("");
  const [isMuted, setIsMuted] = useState(false);
  
  // Refs for WebSocket and audio management
  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const currentAudioSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const isPlayingAudioRef = useRef(false);
  
  // Refs for recording and VAD
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const isRecordingRef = useRef(false);
  const lastSpeechTimeRef = useRef<number>(0);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const vadCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const shouldStartRecordingRef = useRef(false); // Flag to start recording after connection
  
  // VAD Configuration (same as src.main: NO_SPEECH_THRESHOLD = 1.0 second)
  const SILENCE_THRESHOLD_MS = 1000; // 1 second of silence triggers send
  const VAD_CHECK_INTERVAL_MS = 100; // Check audio level every 100ms
  const SPEECH_THRESHOLD = 0.02; // Audio level threshold to detect speech (increased to reduce sensitivity)

  /**
   * WebSocket connection management
   * Uses correct URL format: ws://localhost:8000/ws/voice?user_id={userId}
   */
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setVoiceState("connecting");
    const wsUrl = `ws://localhost:8000/ws/voice?user_id=${userId}`;
    logger.wsConnect(wsUrl);

    try {
      // Correct WebSocket URL format with user_id query parameter
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        logger.info('ws', 'WebSocket connection opened');
        setIsConnected(true);
        setVoiceState("idle");
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        logger.wsMessageReceived(message.event, message.data?.session_id);
        handleWebSocketMessage(message);
      };

      ws.onclose = () => {
        logger.wsDisconnect();
        setIsConnected(false);
        setVoiceState("idle");
        wsRef.current = null;
        sessionIdRef.current = null;
      };

      ws.onerror = (error) => {
        logger.wsError(error);
        onError?.("Connection error. Please try again.");
      };

    } catch (error) {
      console.error("❌ Failed to connect:", error);
      setVoiceState("idle");
      onError?.("Failed to connect to voice service.");
    }
  }, [userId, onError]);

  /**
   * Handle incoming WebSocket messages
   */
  const handleWebSocketMessage = useCallback((message: any) => {
    switch (message.event) {
      case 'connected':
        sessionIdRef.current = message.data.session_id;
        logger.wsConnected(sessionIdRef.current);
        // If user clicked the button while connecting, transition to listening state
        // The useEffect will handle starting the actual recording
        if (shouldStartRecordingRef.current) {
          shouldStartRecordingRef.current = false;
          setVoiceState("listening");
        }
        break;

      case 'transcription':
        const transcription = message.data.text;
        setCurrentTranscription(transcription);
        onTranscription?.(transcription);
        logger.transcriptionReceived(transcription);
        break;

      case 'voice_response':
      case 'agent_response':
        const response = message.data.text;
        setCurrentResponse(response);
        onResponse?.(response);
        logger.responseReceived(response);
        break;

      case 'tts_chunk':
        handleTTSChunk(message.data);
        break;

      case 'streaming_complete':
        console.log("✅ TTS streaming complete");
        // Back to listening after agent finishes speaking
        if (voiceState === "speaking") {
          setVoiceState("listening");
        }
        break;

      case 'streaming_interrupted':
        console.log("🛑 TTS streaming interrupted by user");
        stopAudioPlayback();
        break;

      case 'packet_interruption':
        console.log("🚨 Backend detected new question, interrupting");
        stopAudioPlayback();
        break;

      case 'error':
        console.error("❌ Backend error:", message.data);
        onError?.(message.data.message || "An error occurred");
        break;

      default:
        console.warn("⚠️ Unknown event:", message.event);
    }
  }, [onTranscription, onResponse, onError, voiceState]);

  /**
   * Handle TTS audio chunks from backend
   */
  const handleTTSChunk = useCallback(async (data: any) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }

    try {
      // Decode base64 audio chunk
      const audioData = base64ToArrayBuffer(data.audio_chunk);
      audioQueueRef.current.push(audioData);
      
      // Start playing if not already playing
      if (!isPlayingAudioRef.current) {
        setVoiceState("speaking");
        playNextAudioChunk();
      }
    } catch (error) {
      console.error("❌ Error handling TTS chunk:", error);
    }
  }, []);

  /**
   * Play next audio chunk from queue
   */
  const playNextAudioChunk = useCallback(async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingAudioRef.current = false;
      if (voiceState === "speaking") {
        setVoiceState("listening");
      }
      return;
    }

    isPlayingAudioRef.current = true;
    const audioData = audioQueueRef.current.shift()!;

    try {
      const audioBuffer = await audioContextRef.current!.decodeAudioData(audioData);
      const source = audioContextRef.current!.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current!.destination);
      
      source.onended = () => {
        currentAudioSourceRef.current = null;
        playNextAudioChunk();
      };
      
      currentAudioSourceRef.current = source;
      source.start(0);
    } catch (error) {
      console.error("❌ Error playing audio:", error);
      isPlayingAudioRef.current = false;
      playNextAudioChunk();
    }
  }, [voiceState]);

  /**
   * Stop audio playback immediately (for interruption)
   */
  const stopAudioPlayback = useCallback(() => {
    if (currentAudioSourceRef.current) {
      try {
        currentAudioSourceRef.current.stop();
        currentAudioSourceRef.current.disconnect();
      } catch (e) {
        // Already stopped
      }
      currentAudioSourceRef.current = null;
    }
    audioQueueRef.current = [];
    isPlayingAudioRef.current = false;
    
    if (voiceState === "speaking") {
      setVoiceState("listening");
    }
  }, [voiceState]);

  /**
   * Send interrupt signal to backend
   */
  const sendInterruptSignal = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN && sessionIdRef.current) {
      wsRef.current.send(JSON.stringify({
        event: "interrupt",
        data: {
          session_id: sessionIdRef.current,
          reason: "user_started_speaking"
        }
      }));
      console.log("🛑 Interrupt signal sent to backend");
    }
  }, []);

  /**
   * Voice Activity Detection (VAD)
   * Detects when user is speaking by analyzing audio level
   */
  const checkVoiceActivity = useCallback((audioData: Float32Array): boolean => {
    let sum = 0;
    for (let i = 0; i < audioData.length; i++) {
      sum += Math.abs(audioData[i]);
    }
    const average = sum / audioData.length;

    // Log audio level every 2 seconds for debugging
    if (Date.now() % 2000 < 250) {
      console.log(`🎙️ Audio level: ${average.toFixed(4)} (threshold: ${SPEECH_THRESHOLD})`);
    }

    // Return true if audio level exceeds threshold (user is speaking)
    return average > SPEECH_THRESHOLD;
  }, []);

  /**
   * Start recording with VAD
   * Continuously records audio and monitors for voice activity
   */
  const startRecording = useCallback(async () => {
    if (isRecordingRef.current) {
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      mediaStreamRef.current = stream;
      
      // Create MediaRecorder for audio capture
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      mediaRecorderRef.current = mediaRecorder;
      
      // Set up audio analyzer for VAD
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);
      
      const bufferLength = analyser.fftSize;
      const dataArray = new Float32Array(bufferLength);
      
      // Start recording
      audioChunksRef.current = [];
      lastSpeechTimeRef.current = Date.now(); // Initialize to current time
      mediaRecorder.start(100); // Request data every 100ms for continuous streaming
      isRecordingRef.current = true;
      console.log("🎤 Recording started with VAD");
      
      // Handle recorded data
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      // VAD check loop (~3-4 Hz)
      vadCheckIntervalRef.current = setInterval(() => {
        analyser.getFloatTimeDomainData(dataArray);
        const isSpeaking = checkVoiceActivity(dataArray);
        
        if (isSpeaking) {
          // User is speaking
          lastSpeechTimeRef.current = Date.now();

          // If agent was speaking, interrupt immediately
          if (isPlayingAudioRef.current) {
            console.log("🚨 User started speaking, interrupting agent");
            stopAudioPlayback();
            sendInterruptSignal();
          }

          // Clear any pending silence timer
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        } else {
          // User is silent
          const silenceDuration = Date.now() - lastSpeechTimeRef.current;

          // Log silence duration every 2 seconds for debugging
          if (Date.now() % 2000 < 250 && audioChunksRef.current.length > 0) {
            console.log(`🤐 Silence: ${(silenceDuration / 1000).toFixed(1)}s, chunks: ${audioChunksRef.current.length}`);
          }

          // If silence exceeds threshold and we have chunks to send
          if (silenceDuration >= SILENCE_THRESHOLD_MS && audioChunksRef.current.length > 0) {

            console.log(`📤 Silence threshold reached (${silenceDuration}ms), sending ${audioChunksRef.current.length} chunks immediately`);

            // Send immediately when silence threshold is reached
            sendAudioToBackend();

            // Reset last speech time to prevent multiple sends
            lastSpeechTimeRef.current = Date.now();
          }
        }
      }, 250); // 4Hz checks to reduce message frequency
      
    } catch (error) {
      console.error("❌ Error starting recording:", error);
      onError?.("Microphone access denied or error occurred");
      isRecordingRef.current = false;
    }
  }, [checkVoiceActivity, stopAudioPlayback, sendInterruptSignal, onError]);

  /**
   * Stop recording
   */
  const stopRecording = useCallback(() => {
    if (!isRecordingRef.current) {
      return;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    if (vadCheckIntervalRef.current) {
      clearInterval(vadCheckIntervalRef.current);
      vadCheckIntervalRef.current = null;
    }
    
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    
    isRecordingRef.current = false;
    console.log("🔇 Recording stopped");
  }, []);

  /**
   * Send recorded audio to backend
   * Called after detecting 1 second of silence (same as src.main)
   */
  const sendAudioToBackend = useCallback(async () => {
    if (audioChunksRef.current.length === 0 || !sessionIdRef.current) {
      return;
    }

    logger.vadSendTriggered();
    
    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' });
    audioChunksRef.current = []; // Clear chunks
    
    try {
      // Use the new audio encoder with compression enabled
      const encodedMessage = await audioEncoder.encodeBlob(audioBlob, {
        format: 'webm',
        sampleRate: 48000,
        isFinal: true,
        sessionId: sessionIdRef.current,
        userId: userId,
        compress: true, // Enable compression
        codec: 'opus' // Use Opus for best compression
      });
      
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(encodedMessage));
        logger.audioChunkSent(audioBlob.size, sessionIdRef.current);
        logger.wsMessageSent("audio_chunk", sessionIdRef.current);
      }
    } catch (error) {
      console.error("❌ Error encoding audio:", error);
      onError?.("Failed to encode audio for transmission");
    }
  }, [audioEncoder, userId, onError]);

  /**
   * Start voice interaction
   */
  const startVoiceInteraction = useCallback(async () => {
    // If not connected, open WS and set flag to start recording after connection
    if (!isConnected || !sessionIdRef.current) {
      setVoiceState("connecting");
      shouldStartRecordingRef.current = true; // Flag to start recording after connection
      connectWebSocket();
      return;
    }

    // Already connected with a valid session
    setVoiceState("listening");
    startRecording();
  }, [isConnected, connectWebSocket, startRecording]);

  /**
   * Stop voice interaction
   */
  const stopVoiceInteraction = useCallback(() => {
    stopRecording();
    stopAudioPlayback();
    setVoiceState("idle");
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }
  }, [stopRecording, stopAudioPlayback]);

  /**
   * Handle recording based on voice state
   */
  useEffect(() => {
    if (voiceState === "listening" && !isRecordingRef.current && isConnected) {
      // Start recording when transitioning to listening state
      startRecording().catch((error) => {
        console.error("Failed to start recording:", error);
        onError?.("Microphone access denied or not available");
        setVoiceState("idle");
      });
    } else if (voiceState !== "listening" && isRecordingRef.current) {
      // Stop recording when leaving listening state
      stopRecording();
    }
  }, [voiceState, isConnected, onError]);

  /**
   * Cleanup on unmount ONLY (empty dependency array)
   */
  useEffect(() => {
    return () => {
      // Cleanup only on unmount, not on every render
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }

      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
      }

      if (isPlayingAudioRef.current && currentAudioSourceRef.current) {
        currentAudioSourceRef.current.stop();
      }

      if (wsRef.current) {
        wsRef.current.close();
      }

      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []); // Empty dependency array = cleanup only on unmount

  /**
   * Helper: Convert base64 to ArrayBuffer
   */
  const base64ToArrayBuffer = (base64: string): ArrayBuffer => {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  };

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Voice Button */}
      <div className="relative">
        <Button
          size="lg"
          variant={voiceState === "idle" ? "default" : "destructive"}
          className={cn(
            "h-24 w-24 rounded-full transition-all duration-300",
            voiceState === "listening" && "animate-pulse bg-blue-500 hover:bg-blue-600",
            voiceState === "speaking" && "bg-green-500 hover:bg-green-600",
            voiceState === "connecting" && "bg-yellow-500 hover:bg-yellow-600"
          )}
          onClick={voiceState === "idle" ? startVoiceInteraction : stopVoiceInteraction}
        >
          {voiceState === "idle" ? (
            <Mic className="h-8 w-8" />
          ) : (
            <MicOff className="h-8 w-8" />
          )}
        </Button>
        
        {/* Connection indicator */}
        <div 
          className={cn(
            "absolute top-0 right-0 h-4 w-4 rounded-full border-2 border-white",
            isConnected ? "bg-green-500" : "bg-red-500"
          )}
        />
      </div>

      {/* Status Text */}
      <div className="text-center">
        <p className="text-lg font-medium">
          {voiceState === "idle" && "Click to start conversation"}
          {voiceState === "connecting" && "Connecting..."}
          {voiceState === "listening" && "Listening... (speak naturally)"}
          {voiceState === "speaking" && "Agent is speaking..."}
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          {voiceState === "listening" && "I'll automatically send when you stop talking (1 sec silence)"}
          {voiceState === "speaking" && "Start speaking to interrupt"}
        </p>
      </div>

      {/* Transcription Display */}
      {currentTranscription && (
        <Card className="w-full max-w-md p-4 bg-blue-50">
          <p className="text-sm font-medium text-blue-900">You said:</p>
          <p className="text-sm text-blue-700 mt-1">{currentTranscription}</p>
        </Card>
      )}

      {/* Response Display */}
      {currentResponse && (
        <Card className="w-full max-w-md p-4 bg-green-50">
          <p className="text-sm font-medium text-green-900">Agent:</p>
          <p className="text-sm text-green-700 mt-1">{currentResponse}</p>
        </Card>
      )}
    </div>
  );
}
