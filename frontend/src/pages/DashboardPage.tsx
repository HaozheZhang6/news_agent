import { useState } from "react";
import { VoiceButton } from "../components/VoiceButton";
import { QuickCommands } from "../components/QuickCommands";
import { StatusIndicators } from "../components/StatusIndicators";
import { Card } from "../components/ui/card";
import { WatchlistCard } from "../components/WatchlistCard";
import { Button } from "../components/ui/button";
import { User, History, Settings, LogOut } from "lucide-react";
import { useAuth } from "../lib/auth-context";

type VoiceState = "idle" | "listening" | "speaking";

interface DashboardPageProps {
  onNavigate: (page: "dashboard" | "profile" | "history") => void;
}

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [isConnected, setIsConnected] = useState(true);
  const { user, logout } = useAuth();

  const handleVoiceButtonClick = () => {
    if (voiceState === "idle") {
      setVoiceState("listening");
      // Simulate listening -> speaking transition
      setTimeout(() => setVoiceState("speaking"), 2000);
      setTimeout(() => setVoiceState("idle"), 5000);
    } else {
      setVoiceState("idle");
    }
  };

  const handleQuickCommand = (command: string) => {
    console.log("Quick command:", command);
    setVoiceState("listening");
    setTimeout(() => setVoiceState("speaking"), 1500);
    setTimeout(() => setVoiceState("idle"), 4000);
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
                Tap the button to start a conversation
              </p>
            </div>

            <VoiceButton state={voiceState} onClick={handleVoiceButtonClick} />

            {voiceState !== "idle" && (
              <Card className="w-full max-w-md p-6 animate-in fade-in slide-in-from-bottom-4">
                <p className="text-center text-muted-foreground">
                  {voiceState === "listening" && "I'm listening..."}
                  {voiceState === "speaking" && "Here's what I found for you..."}
                </p>
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
