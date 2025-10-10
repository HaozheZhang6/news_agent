import { useState, useEffect } from "react";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Slider } from "../components/ui/slider";
import { Switch } from "../components/ui/switch";
import { InterestCard } from "../components/InterestCard";
import { StockWatchlistItem } from "../components/StockWatchlistItem";
import { ArrowLeft, Plus, TrendingUp, Newspaper, DollarSign, Briefcase, Globe, Heart, Cpu, Zap, Music, Book } from "lucide-react";
import { useProfile } from "../lib/profile-context";
const API_BASE = import.meta.env.VITE_API_URL as string | undefined;
const DEMO_USER_ID = (import.meta.env.VITE_DEMO_USER_ID as string | undefined) || '03f6b167-0c4d-4983-a380-54b8eb42f830';
import { toast } from "sonner@2.0.3";

interface ProfilePageProps {
  onBack: () => void;
}

export function ProfilePage({ onBack }: ProfilePageProps) {
  const { profile, updateProfile, isLoading } = useProfile();
  const [newStock, setNewStock] = useState("");
  const [localInterests, setLocalInterests] = useState(profile?.interests || {});
  const [localWatchlist, setLocalWatchlist] = useState(profile?.watchlist || []);
  const [localSpeechRate, setLocalSpeechRate] = useState([profile?.settings.speechRate || 1.0]);
  const [localInterruptionSensitivity, setLocalInterruptionSensitivity] = useState([profile?.settings.interruptionSensitivity || 50]);
  const [localNotifications, setLocalNotifications] = useState(profile?.notifications || {
    marketAlerts: true,
    newsDigest: true,
    watchlistUpdates: true,
    dailyBrief: false,
  });

  useEffect(() => {
    if (profile) {
      setLocalInterests(profile.interests);
      setLocalWatchlist(profile.watchlist);
      setLocalSpeechRate([profile.settings.speechRate]);
      setLocalInterruptionSensitivity([profile.settings.interruptionSensitivity]);
      setLocalNotifications(profile.notifications);
    }
  }, [profile]);

  const interestCategories = [
    { id: "technology", icon: Cpu, title: "Technology", description: "Tech news, AI, gadgets" },
    { id: "finance", icon: DollarSign, title: "Finance", description: "Markets, crypto, economics" },
    { id: "business", icon: Briefcase, title: "Business", description: "Corporate news, startups" },
    { id: "health", icon: Heart, title: "Health", description: "Medical, wellness, fitness" },
    { id: "entertainment", icon: Zap, title: "Entertainment", description: "Movies, TV, celebrities" },
    { id: "sports", icon: TrendingUp, title: "Sports", description: "All sports coverage" },
    { id: "science", icon: Globe, title: "Science", description: "Research, discoveries" },
    { id: "politics", icon: Newspaper, title: "Politics", description: "Government, policy" },
    { id: "music", icon: Music, title: "Music", description: "Artists, albums, concerts" },
    { id: "books", icon: Book, title: "Books", description: "Literature, authors" },
  ];

  const toggleInterest = async (id: string) => {
    const updatedInterests = { ...localInterests, [id]: !localInterests[id] };
    setLocalInterests(updatedInterests);
    // Map keyed interests -> array of topics true
    const topics = Object.entries(updatedInterests)
      .filter(([, v]) => Boolean(v))
      .map(([k]) => k);
    if (!API_BASE) return;
    try {
      const userId = DEMO_USER_ID || 'demo-user-id';
      const res = await fetch(`${API_BASE}/api/user/preferences?user_id=${encodeURIComponent(userId)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preferred_topics: topics })
      });
      if (!res.ok) throw new Error('save failed');
      toast.success("Interest updated");
    } catch (error) {
      toast.error("Failed to update interest");
    }
  };

  const addStock = async () => {
    if (newStock.trim()) {
      const newStockItem = {
        symbol: newStock.toUpperCase(),
        name: `${newStock.toUpperCase()} Company`,
        price: Math.random() * 500,
        change: (Math.random() - 0.5) * 10,
        changePercent: (Math.random() - 0.5) * 5,
      };
      const updatedWatchlist = [...localWatchlist, newStockItem];
      setLocalWatchlist(updatedWatchlist);
      setNewStock("");
      try {
        await updateProfile({ watchlist: updatedWatchlist });
        toast.success("Stock added to watchlist");
      } catch (error) {
        toast.error("Failed to add stock");
      }
    }
  };

  const removeStock = async (symbol: string) => {
    const updatedWatchlist = localWatchlist.filter(s => s.symbol !== symbol);
    setLocalWatchlist(updatedWatchlist);
    try {
      await updateProfile({ watchlist: updatedWatchlist });
      toast.success("Stock removed from watchlist");
    } catch (error) {
      toast.error("Failed to remove stock");
    }
  };

  const updateSettings = async () => {
    try {
      await updateProfile({
        settings: {
          speechRate: localSpeechRate[0],
          interruptionSensitivity: localInterruptionSensitivity[0],
          voiceType: 'professional'
        }
      });
      toast.success("Settings updated");
    } catch (error) {
      toast.error("Failed to update settings");
    }
  };

  const updateNotification = async (key: string, value: boolean) => {
    const updatedNotifications = { ...localNotifications, [key]: value };
    setLocalNotifications(updatedNotifications);
    try {
      await updateProfile({ notifications: updatedNotifications });
    } catch (error) {
      toast.error("Failed to update notification");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <p>Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={onBack}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h2>Profile Settings</h2>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        <Tabs defaultValue="interests" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="interests">Interests</TabsTrigger>
            <TabsTrigger value="watchlist">Watchlist</TabsTrigger>
            <TabsTrigger value="voice">Voice</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
          </TabsList>

          {/* Interests Tab */}
          <TabsContent value="interests" className="space-y-6">
            <Card className="p-6">
              <h3 className="mb-2">Your Interests</h3>
              <p className="text-muted-foreground mb-6">
                Select topics you want to hear about in your daily briefings
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {interestCategories.map((category) => (
                  <InterestCard
                    key={category.id}
                    icon={category.icon}
                    title={category.title}
                    description={category.description}
                    enabled={localInterests[category.id] || false}
                    onToggle={() => toggleInterest(category.id)}
                  />
                ))}
              </div>
            </Card>
          </TabsContent>

          {/* Watchlist Tab */}
          <TabsContent value="watchlist" className="space-y-6">
            <Card className="p-6">
              <h3 className="mb-2">Stock Watchlist</h3>
              <p className="text-muted-foreground mb-6">
                Add stocks you want to track in your voice briefings
              </p>
              
              <div className="flex gap-2 mb-6">
                <Input
                  placeholder="Enter stock symbol (e.g., AAPL)"
                  value={newStock}
                  onChange={(e) => setNewStock(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addStock()}
                />
                <Button onClick={addStock}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add
                </Button>
              </div>

              <div className="space-y-3">
                {localWatchlist.map((stock) => (
                  <StockWatchlistItem
                    key={stock.symbol}
                    {...stock}
                    onRemove={() => removeStock(stock.symbol)}
                  />
                ))}
              </div>
            </Card>
          </TabsContent>

          {/* Voice Settings Tab */}
          <TabsContent value="voice" className="space-y-6">
            <Card className="p-6">
              <h3 className="mb-6">Voice Settings</h3>
              
              <div className="space-y-8">
                <div>
                  <div className="flex justify-between mb-3">
                    <Label>Speech Rate</Label>
                    <span className="text-sm text-muted-foreground">{localSpeechRate[0].toFixed(1)}x</span>
                  </div>
                  <Slider
                    value={localSpeechRate}
                    onValueChange={(value) => {
                      setLocalSpeechRate(value);
                      updateSettings();
                    }}
                    min={0.5}
                    max={2.0}
                    step={0.1}
                  />
                  <p className="text-sm text-muted-foreground mt-2">
                    Adjust how fast the voice agent speaks
                  </p>
                </div>

                <div>
                  <div className="flex justify-between mb-3">
                    <Label>Interruption Sensitivity</Label>
                    <span className="text-sm text-muted-foreground">{localInterruptionSensitivity[0]}%</span>
                  </div>
                  <Slider
                    value={localInterruptionSensitivity}
                    onValueChange={(value) => {
                      setLocalInterruptionSensitivity(value);
                      updateSettings();
                    }}
                    min={0}
                    max={100}
                    step={10}
                  />
                  <p className="text-sm text-muted-foreground mt-2">
                    How easily you can interrupt the agent while it's speaking
                  </p>
                </div>

                <div>
                  <Label className="mb-3 block">Voice Type</Label>
                  <div className="grid grid-cols-2 gap-3">
                    <Button variant="outline" className="justify-start">
                      Professional (Default)
                    </Button>
                    <Button variant="outline" className="justify-start">
                      Casual
                    </Button>
                    <Button variant="outline" className="justify-start">
                      Energetic
                    </Button>
                    <Button variant="outline" className="justify-start">
                      Calm
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications" className="space-y-6">
            <Card className="p-6">
              <h3 className="mb-2">Notification Preferences</h3>
              <p className="text-muted-foreground mb-6">
                Choose what notifications you'd like to receive
              </p>

              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b">
                  <div>
                    <p>Market Alerts</p>
                    <p className="text-sm text-muted-foreground">
                      Significant market movements and events
                    </p>
                  </div>
                  <Switch
                    checked={localNotifications.marketAlerts}
                    onCheckedChange={(checked) => updateNotification('marketAlerts', checked)}
                  />
                </div>

                <div className="flex items-center justify-between py-3 border-b">
                  <div>
                    <p>News Digest</p>
                    <p className="text-sm text-muted-foreground">
                      Daily summary of news in your interests
                    </p>
                  </div>
                  <Switch
                    checked={localNotifications.newsDigest}
                    onCheckedChange={(checked) => updateNotification('newsDigest', checked)}
                  />
                </div>

                <div className="flex items-center justify-between py-3 border-b">
                  <div>
                    <p>Watchlist Updates</p>
                    <p className="text-sm text-muted-foreground">
                      Price alerts for your watchlist stocks
                    </p>
                  </div>
                  <Switch
                    checked={localNotifications.watchlistUpdates}
                    onCheckedChange={(checked) => updateNotification('watchlistUpdates', checked)}
                  />
                </div>

                <div className="flex items-center justify-between py-3">
                  <div>
                    <p>Daily Brief Reminder</p>
                    <p className="text-sm text-muted-foreground">
                      Reminder to get your daily briefing
                    </p>
                  </div>
                  <Switch
                    checked={localNotifications.dailyBrief}
                    onCheckedChange={(checked) => updateNotification('dailyBrief', checked)}
                  />
                </div>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
