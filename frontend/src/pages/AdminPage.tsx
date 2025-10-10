import { useState, useEffect } from "react";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ArrowLeft, Users, Database, CheckCircle, XCircle, Activity } from "lucide-react";
import { projectId, publicAnonKey } from "../utils/supabase/info";
import { toast } from "sonner@2.0.3";

interface AdminPageProps {
  onBack: () => void;
}

interface SeededUser {
  email: string;
  name: string;
  id: string;
}

interface HealthCheck {
  status: string;
  database: {
    auth: string;
    storage: string;
    note: string;
  };
  endpoints: string[];
}

export function AdminPage({ onBack }: AdminPageProps) {
  const [isSeeding, setIsSeeding] = useState(false);
  const [seededUsers, setSeededUsers] = useState<SeededUser[]>([]);
  const [hasSeeded, setHasSeeded] = useState(false);
  const [healthCheck, setHealthCheck] = useState<HealthCheck | null>(null);

  useEffect(() => {
    // Fetch health check on mount
    fetchHealthCheck();
  }, []);

  const fetchHealthCheck = async () => {
    try {
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-19e78e3b/health`,
        {
          headers: {
            'Authorization': `Bearer ${publicAnonKey}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setHealthCheck(data);
      }
    } catch (error) {
      console.error('Error fetching health check:', error);
    }
  };

  const handleSeedUsers = async () => {
    setIsSeeding(true);
    try {
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-19e78e3b/seed-users`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${publicAnonKey}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setSeededUsers(data.users || []);
        setHasSeeded(true);
        toast.success(data.message || 'Users seeded successfully');
      } else {
        const error = await response.json();
        toast.error(error.error || 'Failed to seed users');
      }
    } catch (error) {
      console.error('Error seeding users:', error);
      toast.error('Failed to seed users');
    } finally {
      setIsSeeding(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={onBack}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h2>Admin Panel</h2>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Health Check */}
          {healthCheck && (
            <Card className="p-6 bg-green-50 border-green-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-green-100">
                  <Activity className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h3 className="mb-1">System Status: {healthCheck.status.toUpperCase()}</h3>
                  <p className="text-sm text-muted-foreground">{healthCheck.database.note}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 bg-white rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Table Used</p>
                  <p className="text-sm font-mono">{healthCheck.database.users}</p>
                </div>
                <div className="p-3 bg-white rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Data Storage</p>
                  <p className="text-sm font-mono">{healthCheck.database.storage}</p>
                </div>
              </div>
            </Card>
          )}

          {/* Seed Users Section */}
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-primary/10">
                <Database className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 className="mb-1">Seed Test Users</h3>
                <p className="text-sm text-muted-foreground">
                  Generate test users with sample profiles and conversation history
                </p>
              </div>
            </div>

            <Button 
              onClick={handleSeedUsers} 
              disabled={isSeeding}
              className="w-full"
            >
              {isSeeding ? 'Seeding Users...' : 'Seed Test Users'}
            </Button>

            {hasSeeded && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <p className="text-sm text-green-800">Successfully seeded users!</p>
                </div>
                {seededUsers.length > 0 && (
                  <p className="text-xs text-green-700 mt-1">
                    Created {seededUsers.length} users
                  </p>
                )}
              </div>
            )}
          </Card>

          {/* Test Users List */}
          {seededUsers.length > 0 && (
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Users className="w-5 h-5 text-primary" />
                </div>
                <h3>Seeded Test Users</h3>
              </div>

              <div className="space-y-3">
                {seededUsers.map((user) => (
                  <div 
                    key={user.id}
                    className="flex items-center justify-between p-3 bg-muted rounded-lg"
                  >
                    <div>
                      <p className="mb-1">{user.name}</p>
                      <p className="text-sm text-muted-foreground font-mono">{user.email}</p>
                    </div>
                    <Badge variant="secondary">Active</Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Predefined Test Accounts */}
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-primary/10">
                <Users className="w-5 h-5 text-primary" />
              </div>
              <h3>Test Accounts</h3>
            </div>

            <p className="text-sm text-muted-foreground mb-4">
              After seeding, you can use these credentials to log in:
            </p>

            <div className="space-y-3">
              {[
                { email: 'demo@voiceagent.com', password: 'demo123', name: 'Demo User' },
                { email: 'alice@example.com', password: 'password123', name: 'Alice Johnson' },
                { email: 'bob@example.com', password: 'password123', name: 'Bob Smith' },
                { email: 'carol@example.com', password: 'password123', name: 'Carol Davis' },
                { email: 'david@example.com', password: 'password123', name: 'David Wilson' },
              ].map((account) => (
                <div 
                  key={account.email}
                  className="p-3 bg-muted rounded-lg"
                >
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p className="text-muted-foreground">Email:</p>
                      <p className="font-mono">{account.email}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Password:</p>
                      <p className="font-mono">{account.password}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Database Schema */}
          <Card className="p-6 bg-purple-50 border-purple-200">
            <h3 className="mb-3">Database Structure</h3>
            <p className="text-sm text-muted-foreground mb-4">
              This application uses <strong>ONLY Supabase's built-in auth.users table</strong> - no custom tables:
            </p>
            
            <div className="space-y-4">
              <div className="p-3 bg-white rounded-lg border">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-4 h-4 text-purple-600" />
                  <p className="text-sm">
                    <code className="bg-purple-100 px-2 py-1 rounded text-purple-800">auth.users</code>
                  </p>
                </div>
                <p className="text-sm text-muted-foreground ml-6">
                  Supabase built-in table
                  <br />
                  <span className="text-xs">Fields: id, email, encrypted_password, user_metadata (JSONB)</span>
                </p>
              </div>

              <div className="p-3 bg-white rounded-lg border">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-4 h-4 text-purple-600" />
                  <p className="text-sm">
                    <code className="bg-purple-100 px-2 py-1 rounded text-purple-800">user_metadata</code>
                  </p>
                </div>
                <p className="text-sm text-muted-foreground ml-6">
                  JSONB field in auth.users
                  <br />
                  <span className="text-xs">
                    Contains: name, profile, conversations
                  </span>
                </p>
              </div>
            </div>
          </Card>

          {/* Instructions */}
          <Card className="p-6 bg-blue-50 border-blue-200">
            <h3 className="mb-2">How to Use</h3>
            <ol className="space-y-2 text-sm text-muted-foreground list-decimal list-inside">
              <li>Click "Seed Test Users" to create accounts in <code>auth.users</code></li>
              <li>Each user has interests, watchlists, and conversations in <code>user_metadata</code></li>
              <li>Log in with any test account using the credentials above</li>
              <li>All data is stored in <code>auth.users.user_metadata</code> JSONB field</li>
              <li>No custom tables created - pure Supabase auth table</li>
            </ol>
          </Card>
        </div>
      </main>
    </div>
  );
}
