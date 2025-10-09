'use client'

import { useState, useEffect } from 'react'
import { Newspaper, TrendingUp, Clock, ExternalLink } from 'lucide-react'
import { useNews } from '@/contexts/NewsContext'
import { useVoice } from '@/contexts/VoiceContext'

export default function NewsDisplay() {
  const { currentNews, isLoading } = useNews()
  const { sendCommand } = useVoice()
  const [selectedNews, setSelectedNews] = useState<number | null>(null)

  const handleTellMeMore = (index: number) => {
    setSelectedNews(index)
    sendCommand(`tell me more about ${index + 1}`)
  }

  const formatTime = (timestamp: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(timestamp)
  }

  const getTopicIcon = (topic?: string) => {
    switch (topic?.toLowerCase()) {
      case 'technology':
        return '💻'
      case 'finance':
        return '💰'
      case 'politics':
        return '🏛️'
      case 'crypto':
        return '₿'
      case 'energy':
        return '⚡'
      default:
        return '📰'
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
        <p className="text-center text-gray-600 dark:text-gray-300 mt-4">
          Loading news...
        </p>
      </div>
    )
  }

  if (currentNews.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="text-center">
          <Newspaper className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No News Yet
          </h3>
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            Ask for news to get started
          </p>
          <button
            onClick={() => sendCommand('tell me the news')}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Get Latest News
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Latest News
        </h2>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <Clock className="w-4 h-4" />
          <span>{formatTime(new Date())}</span>
        </div>
      </div>

      <div className="space-y-4">
        {currentNews.map((item, index) => (
          <div
            key={item.id}
            className={`border rounded-lg p-4 transition-all duration-200 ${
              selectedNews === index
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-lg">{getTopicIcon(item.topic)}</span>
                  <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                    #{index + 1}
                  </span>
                  {item.topic && (
                    <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded">
                      {item.topic}
                    </span>
                  )}
                </div>
                
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  {item.title}
                </h3>
                
                <p className="text-gray-600 dark:text-gray-300 text-sm leading-relaxed">
                  {item.summary}
                </p>
                
                <div className="flex items-center justify-between mt-3">
                  <span className="text-xs text-gray-500">
                    {formatTime(item.timestamp)}
                  </span>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleTellMeMore(index)}
                      className="text-xs bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded transition-colors"
                    >
                      Tell me more
                    </button>
                    <button
                      onClick={() => sendCommand('skip')}
                      className="text-xs bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded transition-colors"
                    >
                      Skip
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Voice Commands Help */}
      <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
          Voice Commands
        </h4>
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-300">
          <div>• "Tell me more" - Deep dive</div>
          <div>• "Skip" - Next item</div>
          <div>• "Stop" - Interrupt</div>
          <div>• "Stock prices" - Market data</div>
        </div>
      </div>
    </div>
  )
}
