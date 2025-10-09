'use client'

import { useState } from 'react'
import { MessageCircle, User, Bot, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import { useNews } from '@/contexts/NewsContext'

export default function ConversationHistory() {
  const { conversationHistory } = useNews()
  const [isExpanded, setIsExpanded] = useState(false)

  const formatTime = (timestamp: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(timestamp)
  }

  const formatDate = (timestamp: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(timestamp)
  }

  if (conversationHistory.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center space-x-2 mb-4">
          <MessageCircle className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Conversation History
          </h2>
        </div>
        <div className="text-center py-8">
          <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-300">
            No conversations yet. Start by asking for news!
          </p>
        </div>
      </div>
    )
  }

  const displayHistory = isExpanded ? conversationHistory : conversationHistory.slice(0, 3)

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <MessageCircle className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Conversation History
          </h2>
          <span className="text-sm text-gray-500 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
            {conversationHistory.length}
          </span>
        </div>
        
        {conversationHistory.length > 3 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-700 transition-colors"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="w-4 h-4" />
                <span>Show Less</span>
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                <span>Show All</span>
              </>
            )}
          </button>
        )}
      </div>

      <div className="space-y-4">
        {displayHistory.map((entry, index) => (
          <div key={entry.id} className="border-l-4 border-blue-500 pl-4 py-2">
            {/* User Input */}
            <div className="flex items-start space-x-3 mb-2">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    You
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatTime(entry.timestamp)}
                  </span>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {entry.userInput}
                </p>
              </div>
            </div>

            {/* Agent Response */}
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    Agent
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatTime(entry.timestamp)}
                  </span>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {entry.agentResponse}
                </p>
                
                {/* News Items if available */}
                {entry.newsItems && entry.newsItems.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {entry.newsItems.map((newsItem, newsIndex) => (
                      <div key={newsItem.id} className="text-xs bg-gray-50 dark:bg-gray-700 p-2 rounded">
                        <div className="font-medium text-gray-900 dark:text-white">
                          {newsItem.title}
                        </div>
                        <div className="text-gray-600 dark:text-gray-300">
                          {newsItem.summary}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {conversationHistory.length}
            </div>
            <div className="text-xs text-gray-500">Conversations</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {conversationHistory.reduce((acc, entry) => acc + (entry.newsItems?.length || 0), 0)}
            </div>
            <div className="text-xs text-gray-500">News Items</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {conversationHistory.length > 0 ? formatDate(conversationHistory[0].timestamp) : 'N/A'}
            </div>
            <div className="text-xs text-gray-500">Last Activity</div>
          </div>
        </div>
      </div>
    </div>
  )
}
