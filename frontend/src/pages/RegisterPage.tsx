import { useState } from "react";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { Separator } from "../components/ui/separator";
import { useAuth } from "../lib/auth-context";
import { Github, Mail } from "lucide-react";

interface RegisterPageProps {
  onSwitchToLogin: () => void;
}

export function RegisterPage({ onSwitchToLogin }: RegisterPageProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      alert("Passwords don't match!");
      return;
    }
    setIsLoading(true);
    try {
      await register(email, password, name);
    } catch (error) {
      console.error("Registration failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="mb-2">Create Account</h1>
          <p className="text-muted-foreground">Get started with your voice agent</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Full Name</Label>
            <Input
              id="name"
              type="text"
              placeholder="John Doe"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="mt-2"
            />
          </div>

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

          <div>
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="mt-2"
            />
          </div>

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Creating account..." : "Create Account"}
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
            onClick={onSwitchToLogin}
          >
            Already have an account? <span className="text-primary">Sign in</span>
          </button>
        </div>
      </Card>
    </div>
  );
}
