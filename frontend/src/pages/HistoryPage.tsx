import { useState, useMemo } from "react";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { ConversationMessage } from "../components/ConversationMessage";
import { ArrowLeft, Search, Filter, BarChart3 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { useConversations } from "../lib/conversation-context";

interface HistoryPageProps {
  onBack: () => void;
}

export function HistoryPage({ onBack }: HistoryPageProps) {
  const { conversations, isLoading } = useConversations();
  const [searchQuery, setSearchQuery] = useState("");

  const filteredConversations = useMemo(() => {
    if (!searchQuery) return conversations;
    return conversations.filter(conv => 
      conv.messages.some(msg => 
        msg.content.toLowerCase().includes(searchQuery.toLowerCase())
      )
    );
  }, [conversations, searchQuery]);

  const stats = useMemo(() => {
    const totalConversations = conversations.length;
    const totalDuration = conversations.reduce((sum, conv) => {
      return sum + (conv.messages.length * 2); // Rough estimate: 2 minutes per message pair
    }, 0);
    const newsBriefings = conversations.filter(conv => 
      conv.messages.some(msg => msg.newsItems && msg.newsItems.length > 0)
    ).length;
    const avgPerDay = Math.round(totalConversations / 7);

    return [
      { label: "Total Conversations", value: totalConversations.toString() },
      { label: "Total Duration", value: `${Math.floor(totalDuration / 60)}h ${totalDuration % 60}m` },
      { label: "News Briefings", value: newsBriefings.toString() },
      { label: "Avg. Per Day", value: avgPerDay.toString() },
    ];
  }, [conversations]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <p>Loading conversation history...</p>
      </div>
    );
  }

  const mockConversations = filteredConversations.length > 0 ? filteredConversations : [
    {
      id: 1,
      date: "Today, 2:30 PM",
      messages: [
        {
          type: "user" as const,
          content: "What's happening in the market today?",
          timestamp: "2:30 PM",
        },
        {
          type: "agent" as const,
          content: "The market is showing mixed signals today. The S&P 500 is up 0.3%, while the Nasdaq is down 0.5%. Tech stocks are seeing some profit-taking after yesterday's rally.",
          timestamp: "2:30 PM",
          newsItems: [
            {
              title: "Tech Stocks Face Headwinds as Fed Signals Rate Stability",
              source: "Bloomberg",
              url: "#",
            },
            {
              title: "Market Analysis: What's Driving Today's Trading",
              source: "CNBC",
              url: "#",
            },
          ],
        },
      ],
    },
    {
      id: 2,
      date: "Today, 9:15 AM",
      messages: [
        {
          type: "user" as const,
          content: "Tell me about my watchlist",
          timestamp: "9:15 AM",
        },
        {
          type: "agent" as const,
          content: "Here's your watchlist update: Apple is up 1.3% at $178.45, Google is down 0.85% at $142.67, and Microsoft is up 1.39% at $412.89. Overall, your watchlist is performing well today.",
          timestamp: "9:15 AM",
        },
      ],
    },
    {
      id: 3,
      date: "Yesterday, 5:45 PM",
      messages: [
        {
          type: "user" as const,
          content: "Give me the latest tech news",
          timestamp: "5:45 PM",
        },
        {
          type: "agent" as const,
          content: "Here are the top tech stories: OpenAI announces new GPT model with improved reasoning, Apple announces new product event for next month, and Meta reports strong quarterly earnings.",
          timestamp: "5:45 PM",
          newsItems: [
            {
              title: "OpenAI Unveils Next-Generation Language Model",
              source: "TechCrunch",
              url: "#",
            },
            {
              title: "Apple September Event: What to Expect",
              source: "The Verge",
              url: "#",
            },
            {
              title: "Meta Beats Earnings Expectations on Strong Ad Revenue",
              source: "Reuters",
              url: "#",
            },
          ],
        },
      ],
    },
  ];



  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={onBack}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h2>Conversation History</h2>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        <Tabs defaultValue="conversations" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="conversations">Conversations</TabsTrigger>
            <TabsTrigger value="statistics">Statistics</TabsTrigger>
          </TabsList>

          {/* Conversations Tab */}
          <TabsContent value="conversations" className="space-y-6">
            {/* Search and Filter */}
            <Card className="p-4">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search conversations..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Button variant="outline">
                  <Filter className="w-4 h-4 mr-2" />
                  Filter
                </Button>
              </div>
            </Card>

            {/* Conversation Timeline */}
            <div className="space-y-6">
              {displayConversations.length === 0 ? (
                <Card className="p-12 text-center">
                  <p className="text-muted-foreground mb-2">No conversations yet</p>
                  <p className="text-sm text-muted-foreground">Start a conversation on the dashboard to see your history here</p>
                </Card>
              ) : (
                displayConversations.map((conversation) => (
                  <Card key={conversation.id} className="p-6">
                    <div className="mb-4 pb-4 border-b">
                      <p className="text-sm text-muted-foreground">{conversation.date}</p>
                    </div>
                    <div className="space-y-6">
                      {conversation.messages.map((message, idx) => (
                        <ConversationMessage
                          key={idx}
                          type={message.type}
                          content={message.content}
                          timestamp={message.timestamp}
                          newsItems={message.newsItems}
                        />
                      ))}
                    </div>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* Statistics Tab */}
          <TabsContent value="statistics" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {stats.map((stat) => (
                <Card key={stat.label} className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-lg bg-primary/10">
                      <BarChart3 className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">{stat.label}</p>
                      <p className="text-2xl mt-1">{stat.value}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            <Card className="p-6">
              <h3 className="mb-4">Usage Over Time</h3>
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                <p>Chart visualization would go here</p>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="mb-4">Most Asked Topics</h3>
              <div className="space-y-3">
                {[
                  { topic: "Market Updates", count: 45, percentage: 65 },
                  { topic: "News Briefings", count: 32, percentage: 48 },
                  { topic: "Watchlist Updates", count: 28, percentage: 42 },
                  { topic: "Tech News", count: 24, percentage: 35 },
                  { topic: "General Questions", count: 18, percentage: 27 },
                ].map((item) => (
                  <div key={item.topic}>
                    <div className="flex justify-between mb-2">
                      <span>{item.topic}</span>
                      <span className="text-muted-foreground">{item.count}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full"
                        style={{ width: `${item.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
