'use client'

import { useState, useEffect } from 'react'
import { Mic, MicOff, Volume2, VolumeX, Play, Pause } from 'lucide-react'
import { useVoice } from '@/contexts/VoiceContext'
import { useNews } from '@/contexts/NewsContext'
import toast from 'react-hot-toast'

export default function VoiceInterface() {
  const { isListening, isSpeaking, isConnected, startListening, stopListening, sendCommand } = useVoice()
  const { setLoading } = useNews()
  const [isRecording, setIsRecording] = useState(false)
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null)

  useEffect(() => {
    // Request microphone permission
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        setAudioStream(stream)
        stream.getTracks().forEach(track => track.stop()) // Stop initial stream
      })
      .catch(error => {
        console.error('Microphone access denied:', error)
        toast.error('Microphone access required for voice interaction')
      })
  }, [])

  const handleStartListening = async () => {
    if (!isConnected) {
      toast.error('Not connected to voice server')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      setAudioStream(stream)
      setIsRecording(true)
      setLoading(true)
      startListening()
      toast.success('Listening...')
    } catch (error) {
      console.error('Failed to start recording:', error)
      toast.error('Failed to access microphone')
    }
  }

  const handleStopListening = () => {
    if (audioStream) {
      audioStream.getTracks().forEach(track => track.stop())
      setAudioStream(null)
    }
    setIsRecording(false)
    setLoading(false)
    stopListening()
    toast.success('Stopped listening')
  }

  const handleInterrupt = () => {
    sendCommand('stop')
    toast.success('Interrupted')
  }

  const handleQuickCommands = (command: string) => {
    sendCommand(command)
    toast.success(`Sent: ${command}`)
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Voice Control
      </h2>

      {/* Main Voice Button */}
      <div className="flex flex-col items-center space-y-4">
        <button
          onClick={isListening ? handleStopListening : handleStartListening}
          disabled={!isConnected}
          className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-200 ${
            isListening 
              ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
              : 'bg-blue-500 hover:bg-blue-600'
          } ${!isConnected ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        >
          {isListening ? (
            <MicOff className="w-8 h-8 text-white" />
          ) : (
            <Mic className="w-8 h-8 text-white" />
          )}
        </button>

        <div className="text-center">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {isListening ? 'Listening...' : isSpeaking ? 'Speaking...' : 'Tap to speak'}
          </p>
          {isConnected && (
            <div className="flex items-center justify-center mt-2">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              <span className="text-xs text-green-600">Connected</span>
            </div>
          )}
        </div>
      </div>

      {/* Interrupt Button */}
      {isSpeaking && (
        <div className="mt-4 flex justify-center">
          <button
            onClick={handleInterrupt}
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <VolumeX className="w-4 h-4" />
            <span>Interrupt</span>
          </button>
        </div>
      )}

      {/* Quick Commands */}
      <div className="mt-6">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Quick Commands
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {[
            'Tell me the news',
            'Stock prices',
            'Tell me more',
            'Stop',
            'Skip',
            'Help'
          ].map((command) => (
            <button
              key={command}
              onClick={() => handleQuickCommands(command)}
              disabled={!isConnected}
              className="text-xs bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 px-3 py-2 rounded transition-colors disabled:opacity-50"
            >
              {command}
            </button>
          ))}
        </div>
      </div>

      {/* Status Indicators */}
      <div className="mt-6 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-300">Listening:</span>
          <div className={`w-3 h-3 rounded-full ${isListening ? 'bg-green-500' : 'bg-gray-300'}`}></div>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-300">Speaking:</span>
          <div className={`w-3 h-3 rounded-full ${isSpeaking ? 'bg-blue-500' : 'bg-gray-300'}`}></div>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-300">Connected:</span>
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
        </div>
      </div>
    </div>
  )
}
