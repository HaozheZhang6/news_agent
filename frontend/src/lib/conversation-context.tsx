import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useAuth } from "./auth-context";
import { projectId } from "../utils/supabase/info";

interface NewsItem {
  title: string;
  source: string;
  url: string;
}

interface Message {
  type: "user" | "agent";
  content: string;
  timestamp: string;
  newsItems?: NewsItem[];
}

interface Conversation {
  id: string;
  date: string;
  messages: Message[];
  timestamp: number;
}

interface ConversationContextType {
  conversations: Conversation[];
  addConversation: (messages: Message[]) => Promise<void>;
  isLoading: boolean;
}

const ConversationContext = createContext<ConversationContextType | undefined>(undefined);

export function ConversationProvider({ children }: { children: ReactNode }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { accessToken, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated && accessToken) {
      fetchConversations();
    } else {
      setConversations([]);
      setIsLoading(false);
    }
  }, [isAuthenticated, accessToken]);

  const fetchConversations = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-19e78e3b/conversations`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const addConversation = async (messages: Message[]) => {
    try {
      const timestamp = Date.now();
      const date = new Date(timestamp).toLocaleString();
      
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-19e78e3b/conversations`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
          body: JSON.stringify({ messages, date }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        const newConversation: Conversation = {
          id: data.id,
          date,
          messages,
          timestamp: data.timestamp,
        };
        setConversations(prev => [newConversation, ...prev]);
      }
    } catch (error) {
      console.error('Error saving conversation:', error);
      throw error;
    }
  };

  return (
    <ConversationContext.Provider value={{ conversations, addConversation, isLoading }}>
      {children}
    </ConversationContext.Provider>
  );
}

export function useConversations() {
  const context = useContext(ConversationContext);
  if (context === undefined) {
    throw new Error("useConversations must be used within a ConversationProvider");
  }
  return context;
}
