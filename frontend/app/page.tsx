'use client'

import { useState, useEffect } from 'react'
import VoiceInterface from '@/components/VoiceInterface'
import NewsDisplay from '@/components/NewsDisplay'
import ConversationHistory from '@/components/ConversationHistory'
import { VoiceProvider } from '@/contexts/VoiceContext'
import { NewsProvider } from '@/contexts/NewsContext'

export default function Home() {
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // Check backend connection
    const checkConnection = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
        setIsConnected(response.ok)
      } catch (error) {
        console.error('Backend connection failed:', error)
        setIsConnected(false)
      }
    }

    checkConnection()
    const interval = setInterval(checkConnection, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <VoiceProvider>
      <NewsProvider>
        <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
          <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                🎙️ Voice News Agent
              </h1>
              <p className="text-lg text-gray-600 dark:text-gray-300">
                AI-powered voice-activated news assistant
              </p>
              <div className="flex items-center justify-center mt-4">
                <div className={`w-3 h-3 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-500">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>

            {/* Main Interface */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Voice Interface */}
              <div className="lg:col-span-1">
                <VoiceInterface />
              </div>

              {/* News Display */}
              <div className="lg:col-span-2">
                <NewsDisplay />
              </div>
            </div>

            {/* Conversation History */}
            <div className="mt-8">
              <ConversationHistory />
            </div>
          </div>
        </main>
      </NewsProvider>
    </VoiceProvider>
  )
}
