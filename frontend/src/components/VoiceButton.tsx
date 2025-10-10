import { Mic, MicOff } from "lucide-react";
import { cn } from "./ui/utils";

type VoiceState = "idle" | "listening" | "speaking";

interface VoiceButtonProps {
  state: VoiceState;
  onClick: () => void;
}

export function VoiceButton({ state, onClick }: VoiceButtonProps) {
  const stateConfig = {
    idle: {
      color: "bg-[#3B82F6] hover:bg-[#2563EB]",
      icon: Mic,
      label: "Start Conversation",
      glow: "shadow-lg shadow-blue-500/50",
    },
    listening: {
      color: "bg-red-500 hover:bg-red-600 animate-pulse",
      icon: Mic,
      label: "Listening...",
      glow: "shadow-lg shadow-red-500/50",
    },
    speaking: {
      color: "bg-green-500 hover:bg-green-600",
      icon: MicOff,
      label: "Speaking...",
      glow: "shadow-lg shadow-green-500/50",
    },
  };

  const config = stateConfig[state];
  const Icon = config.icon;

  return (
    <div className="flex flex-col items-center gap-4">
      <button
        onClick={onClick}
        className={cn(
          "w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300",
          config.color,
          config.glow,
          "active:scale-95"
        )}
        aria-label={config.label}
      >
        <Icon className="w-12 h-12 text-white" />
      </button>
      <span className="text-muted-foreground">{config.label}</span>
    </div>
  );
}
