'use client'

import { useEffect, useState } from "react";
import { Card } from "./ui/card";
import { projectId } from "../utils/supabase/info";

export function WatchlistCard() {
  const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)
    || (import.meta.env.NEXT_PUBLIC_API_URL as string | undefined)
    || 'http://localhost:8000';
  const DEMO_USER_ID = (import.meta.env.VITE_DEMO_USER_ID as string | undefined) || '03f6b167-0c4d-4983-a380-54b8eb42f830';

  const [loading, setLoading] = useState(true);
  const [symbols, setSymbols] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      const userId = DEMO_USER_ID || "demo-user-id";
      try {
        const res = await fetch(`${API_BASE}/api/user/watchlist?user_id=${encodeURIComponent(userId)}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setSymbols(data.watchlist_stocks || []);
      } catch (e: any) {
        setError(e?.message || "Failed to load watchlist");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [API_BASE, DEMO_USER_ID]);

  return (
    <Card className="p-6">
      <h3 className="mb-4">Watchlist</h3>
      {loading ? (
        <div className="text-sm text-muted-foreground">Loading...</div>
      ) : error ? (
        <div className="text-sm text-red-500">{error}</div>
      ) : symbols.length === 0 ? (
        <div className="text-sm text-muted-foreground">No symbols yet.</div>
      ) : (
        <ul className="space-y-2">
          {symbols.map((s) => (
            <li key={s} className="text-sm font-mono">{s}</li>
          ))}
        </ul>
      )}
    </Card>
  );
}


