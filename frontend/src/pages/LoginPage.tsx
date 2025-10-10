import { useState } from "react";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { Separator } from "../components/ui/separator";
import { useAuth } from "../lib/auth-context";
import { Github, Mail, Settings } from "lucide-react";
import { toast } from "sonner@2.0.3";

interface LoginPageProps {
  onSwitchToRegister: () => void;
  onSwitchToAdmin?: () => void;
}

export function LoginPage({ onSwitchToRegister, onSwitchToAdmin }: LoginPageProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await login(email, password);
      toast.success("Welcome back!");
    } catch (error) {
      console.error("Login failed:", error);
      toast.error(error instanceof Error ? error.message : "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-full max-w-md p-8 relative">
        {onSwitchToAdmin && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-4 right-4"
            onClick={onSwitchToAdmin}
          >
            <Settings className="w-5 h-5" />
          </Button>
        )}
        
        <div className="text-center mb-8">
          <h1 className="mb-2">Welcome Back</h1>
          <p className="text-muted-foreground">Sign in to your voice agent account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-2"
            />
          </div>

          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-2"
            />
          </div>

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Signing in..." : "Sign In"}
          </Button>
        </form>

        <div className="my-6">
          <div className="relative">
            <Separator />
            <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-2 text-sm text-muted-foreground">
              Or continue with
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Button 
            variant="outline" 
            type="button"
            onClick={() => {
              alert("To enable Google login, please follow the setup instructions at:\nhttps://supabase.com/docs/guides/auth/social-login/auth-google");
            }}
          >
            <Mail className="w-4 h-4 mr-2" />
            Google
          </Button>
          <Button 
            variant="outline" 
            type="button"
            onClick={() => {
              alert("To enable GitHub login, please follow the setup instructions at:\nhttps://supabase.com/docs/guides/auth/social-login/auth-github");
            }}
          >
            <Github className="w-4 h-4 mr-2" />
            GitHub
          </Button>
        </div>

        <div className="mt-6 text-center text-sm">
          <button
            type="button"
            className="text-muted-foreground hover:text-foreground"
            onClick={onSwitchToRegister}
          >
            Don't have an account? <span className="text-primary">Sign up</span>
          </button>
        </div>

        {onSwitchToAdmin && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-center">
            <p className="text-xs text-blue-800">
              Click the <Settings className="w-3 h-3 inline" /> icon in the top-right to seed test users
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
