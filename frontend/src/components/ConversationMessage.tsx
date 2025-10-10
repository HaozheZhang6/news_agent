import { User, Bot, ExternalLink } from "lucide-react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";

interface NewsItem {
  title: string;
  source: string;
  url: string;
}

interface ConversationMessageProps {
  type: "user" | "agent";
  content: string;
  timestamp: string;
  newsItems?: NewsItem[];
}

export function ConversationMessage({ type, content, timestamp, newsItems }: ConversationMessageProps) {
  const isUser = type === "user";
  
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
        isUser ? "bg-primary" : "bg-[#3B82F6]"
      }`}>
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>
      
      <div className={`flex-1 ${isUser ? "flex flex-col items-end" : ""}`}>
        <Card className={`p-4 max-w-2xl ${isUser ? "bg-primary text-primary-foreground" : ""}`}>
          <p className="whitespace-pre-wrap">{content}</p>
          <p className={`text-xs mt-2 ${isUser ? "text-primary-foreground/70" : "text-muted-foreground"}`}>
            {timestamp}
          </p>
        </Card>
        
        {newsItems && newsItems.length > 0 && (
          <div className="mt-3 space-y-2 max-w-2xl">
            <p className="text-sm text-muted-foreground">Related News:</p>
            {newsItems.map((item, idx) => (
              <Card key={idx} className="p-3">
                <a 
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-start gap-2 hover:underline"
                >
                  <div className="flex-1">
                    <p className="mb-1">{item.title}</p>
                    <Badge variant="secondary" className="text-xs">
                      {item.source}
                    </Badge>
                  </div>
                  <ExternalLink className="w-4 h-4 text-muted-foreground shrink-0" />
                </a>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
