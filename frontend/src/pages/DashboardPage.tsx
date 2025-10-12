import { useState } from "react";
import { ContinuousVoiceInterface } from "../components/ContinuousVoiceInterface";
import { QuickCommands } from "../components/QuickCommands";
import { StatusIndicators } from "../components/StatusIndicators";
import { Card } from "../components/ui/card";
import { WatchlistCard } from "../components/WatchlistCard";
import { Button } from "../components/ui/button";
import { User, History, Settings, LogOut } from "lucide-react";
import { useAuth } from "../lib/auth-context";
import { toast } from "sonner";
import { cn } from "../components/ui/utils";

type VoiceState = "idle" | "listening" | "speaking" | "connecting";

interface DashboardPageProps {
  onNavigate: (page: "dashboard" | "profile" | "history") => void;
}

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [isConnected, setIsConnected] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<Array<{
    id: string;
    type: 'user' | 'agent';
    text: string;
    timestamp: Date;
  }>>([]);
  
  const { user, logout } = useAuth();

  const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };

  const handleTranscription = (text: string) => {
    const newEntry = {
      id: Date.now().toString(),
      type: 'user' as const,
      text,
      timestamp: new Date()
    };
    setConversationHistory(prev => [...prev, newEntry]);
  };

  const handleResponse = (text: string) => {
    const newEntry = {
      id: Date.now().toString(),
      type: 'agent' as const,
      text,
      timestamp: new Date()
    };
    setConversationHistory(prev => [...prev, newEntry]);
  };

  const handleError = (error: string) => {
    toast.error(error);
  };

  const handleQuickCommand = (command: string) => {
    console.log("Quick command:", command);
    // Quick commands will be handled by the continuous voice interface
    toast.info(`Quick command: ${command}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h2>Voice Agent</h2>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onNavigate("profile")}
              >
                <User className="w-5 h-5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onNavigate("history")}
              >
                <History className="w-5 h-5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={logout}
              >
                <LogOut className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Status */}
          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="mb-4">Connection Status</h3>
              <StatusIndicators
                isConnected={isConnected}
                isListening={voiceState === "listening"}
                isSpeaking={voiceState === "speaking"}
              />
            </Card>

            <Card className="p-6">
              <h3 className="mb-4">Today's Summary</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Conversations</span>
                  <span>12</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Duration</span>
                  <span>45 min</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">News Briefings</span>
                  <span>8</span>
                </div>
              </div>
            </Card>
          </div>

          {/* Center Column - Voice Interface */}
          <div className="flex flex-col items-center justify-center gap-8">
            <div className="text-center">
              <h1 className="mb-2">Hey, {user?.name}!</h1>
              <p className="text-muted-foreground">
                Start a continuous conversation with your voice agent
              </p>
            </div>

            <ContinuousVoiceInterface
              userId={user?.id || generateUUID()}
              onTranscription={handleTranscription}
              onResponse={handleResponse}
              onError={handleError}
            />

            {/* Conversation History */}
            {conversationHistory.length > 0 && (
              <Card className="w-full max-w-md p-4">
                <h3 className="mb-3 text-sm font-medium">Recent Conversation</h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {conversationHistory.slice(-5).map((entry) => (
                    <div key={entry.id} className="text-xs">
                      <span className={cn(
                        "font-medium",
                        entry.type === 'user' ? "text-blue-600" : "text-green-600"
                      )}>
                        {entry.type === 'user' ? 'You' : 'Agent'}:
                      </span>
                      <span className="ml-2">{entry.text}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Right Column - Quick Commands & Watchlist */}
          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="mb-4">Quick Commands</h3>
              <QuickCommands onCommand={handleQuickCommand} />
            </Card>

            <Card className="p-6">
              <h3 className="mb-4">Recent Activity</h3>
              <div className="space-y-3">
                <div className="text-sm">
                  <p className="mb-1">Market Update</p>
                  <p className="text-muted-foreground text-xs">2 minutes ago</p>
                </div>
                <div className="text-sm">
                  <p className="mb-1">Watchlist Brief</p>
                  <p className="text-muted-foreground text-xs">15 minutes ago</p>
                </div>
                <div className="text-sm">
                  <p className="mb-1">Daily News</p>
                  <p className="text-muted-foreground text-xs">1 hour ago</p>
                </div>
              </div>
            </Card>

            <WatchlistCard />
          </div>
        </div>
      </main>
    </div>
  );
}
