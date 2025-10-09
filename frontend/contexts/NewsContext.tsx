'use client'

import { createContext, useContext, useState, useCallback } from 'react'

interface NewsItem {
  id: string
  title: string
  summary: string
  timestamp: Date
  topic?: string
}

interface ConversationEntry {
  id: string
  userInput: string
  agentResponse: string
  timestamp: Date
  newsItems?: NewsItem[]
}

interface NewsContextType {
  currentNews: NewsItem[]
  conversationHistory: ConversationEntry[]
  isLoading: boolean
  addNewsItem: (item: NewsItem) => void
  addConversation: (entry: ConversationEntry) => void
  clearNews: () => void
  setLoading: (loading: boolean) => void
}

const NewsContext = createContext<NewsContextType | undefined>(undefined)

export function NewsProvider({ children }: { children: React.ReactNode }) {
  const [currentNews, setCurrentNews] = useState<NewsItem[]>([])
  const [conversationHistory, setConversationHistory] = useState<ConversationEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const addNewsItem = useCallback((item: NewsItem) => {
    setCurrentNews(prev => [item, ...prev].slice(0, 10)) // Keep last 10 items
  }, [])

  const addConversation = useCallback((entry: ConversationEntry) => {
    setConversationHistory(prev => [entry, ...prev].slice(0, 20)) // Keep last 20 conversations
  }, [])

  const clearNews = useCallback(() => {
    setCurrentNews([])
  }, [])

  const setLoading = useCallback((loading: boolean) => {
    setIsLoading(loading)
  }, [])

  return (
    <NewsContext.Provider value={{
      currentNews,
      conversationHistory,
      isLoading,
      addNewsItem,
      addConversation,
      clearNews,
      setLoading
    }}>
      {children}
    </NewsContext.Provider>
  )
}

export function useNews() {
  const context = useContext(NewsContext)
  if (context === undefined) {
    throw new Error('useNews must be used within a NewsProvider')
  }
  return context
}
