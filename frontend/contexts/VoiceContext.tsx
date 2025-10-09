'use client'

import { createContext, useContext, useState, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'

interface VoiceContextType {
  isListening: boolean
  isSpeaking: boolean
  isConnected: boolean
  startListening: () => void
  stopListening: () => void
  sendCommand: (command: string) => void
  socket: Socket | null
}

const VoiceContext = createContext<VoiceContextType | undefined>(undefined)

export function VoiceProvider({ children }: { children: React.ReactNode }) {
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [socket, setSocket] = useState<Socket | null>(null)

  const initializeSocket = useCallback(() => {
    const newSocket = io(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000')
    
    newSocket.on('connect', () => {
      setIsConnected(true)
      console.log('Connected to voice server')
    })

    newSocket.on('disconnect', () => {
      setIsConnected(false)
      console.log('Disconnected from voice server')
    })

    newSocket.on('voice_response', (data) => {
      setIsSpeaking(true)
      // Handle TTS audio playback
      if (data.audioUrl) {
        const audio = new Audio(data.audioUrl)
        audio.play()
        audio.onended = () => setIsSpeaking(false)
      }
    })

    newSocket.on('voice_interrupted', () => {
      setIsSpeaking(false)
      console.log('Voice interrupted')
    })

    newSocket.on('transcription', (data) => {
      console.log('Transcription:', data.text)
    })

    setSocket(newSocket)
    return newSocket
  }, [])

  const startListening = useCallback(() => {
    if (!socket) {
      initializeSocket()
      return
    }
    
    setIsListening(true)
    socket.emit('start_listening')
  }, [socket, initializeSocket])

  const stopListening = useCallback(() => {
    if (socket) {
      setIsListening(false)
      socket.emit('stop_listening')
    }
  }, [socket])

  const sendCommand = useCallback((command: string) => {
    if (socket) {
      socket.emit('voice_command', { command })
    }
  }, [socket])

  return (
    <VoiceContext.Provider value={{
      isListening,
      isSpeaking,
      isConnected,
      startListening,
      stopListening,
      sendCommand,
      socket
    }}>
      {children}
    </VoiceContext.Provider>
  )
}

export function useVoice() {
  const context = useContext(VoiceContext)
  if (context === undefined) {
    throw new Error('useVoice must be used within a VoiceProvider')
  }
  return context
}
