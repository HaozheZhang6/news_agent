import { Button } from "./ui/button";
import { TrendingUp, Newspaper, Briefcase, Radio } from "lucide-react";

interface QuickCommandsProps {
  onCommand: (command: string) => void;
}

export function QuickCommands({ onCommand }: QuickCommandsProps) {
  const commands = [
    { icon: TrendingUp, label: "Market Update", command: "What's happening in the market?" },
    { icon: Newspaper, label: "Latest News", command: "Tell me the latest news" },
    { icon: Briefcase, label: "My Watchlist", command: "Update me on my watchlist" },
    { icon: Radio, label: "Daily Brief", command: "Give me my daily brief" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3">
      {commands.map((cmd) => (
        <Button
          key={cmd.label}
          variant="outline"
          className="h-auto py-4 flex flex-col gap-2 hover:bg-accent"
          onClick={() => onCommand(cmd.command)}
        >
          <cmd.icon className="w-5 h-5" />
          <span className="text-sm">{cmd.label}</span>
        </Button>
      ))}
    </div>
  );
}
