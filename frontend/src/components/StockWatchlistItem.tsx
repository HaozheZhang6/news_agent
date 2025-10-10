import { X, TrendingUp, TrendingDown } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";

interface StockWatchlistItemProps {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  onRemove: () => void;
}

export function StockWatchlistItem({ 
  symbol, 
  name, 
  price, 
  change, 
  changePercent,
  onRemove 
}: StockWatchlistItemProps) {
  const isPositive = change >= 0;
  
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono">{symbol}</span>
            {isPositive ? (
              <TrendingUp className="w-4 h-4 text-green-500" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500" />
            )}
          </div>
          <p className="text-sm text-muted-foreground">{name}</p>
        </div>
        
        <div className="text-right">
          <div className="mb-1">${price.toFixed(2)}</div>
          <div className={isPositive ? "text-green-500 text-sm" : "text-red-500 text-sm"}>
            {isPositive ? "+" : ""}{change.toFixed(2)} ({isPositive ? "+" : ""}{changePercent.toFixed(2)}%)
          </div>
        </div>
        
        <Button
          variant="ghost"
          size="icon"
          onClick={onRemove}
          className="shrink-0"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </Card>
  );
}
