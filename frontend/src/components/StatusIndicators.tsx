import { Wifi, WifiOff, Mic, Volume2 } from "lucide-react";
import { cn } from "./ui/utils";

interface StatusIndicatorsProps {
  isConnected: boolean;
  isListening: boolean;
  isSpeaking: boolean;
}

export function StatusIndicators({ isConnected, isListening, isSpeaking }: StatusIndicatorsProps) {
  return (
    <div className="flex items-center gap-4 px-4 py-3 bg-card border rounded-lg">
      <div className="flex items-center gap-2">
        {isConnected ? (
          <Wifi className="w-4 h-4 text-green-500" />
        ) : (
          <WifiOff className="w-4 h-4 text-red-500" />
        )}
        <span className="text-sm text-muted-foreground">
          {isConnected ? "Connected" : "Disconnected"}
        </span>
      </div>
      
      <div className={cn(
        "flex items-center gap-2",
        isListening ? "text-red-500" : "text-muted-foreground"
      )}>
        <Mic className="w-4 h-4" />
        <span className="text-sm">Listening</span>
      </div>
      
      <div className={cn(
        "flex items-center gap-2",
        isSpeaking ? "text-green-500" : "text-muted-foreground"
      )}>
        <Volume2 className="w-4 h-4" />
        <span className="text-sm">Speaking</span>
      </div>
    </div>
  );
}
