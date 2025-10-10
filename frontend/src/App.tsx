import { useState } from "react";
import { AuthProvider, useAuth } from "./lib/auth-context";
import { ProfileProvider } from "./lib/profile-context";
import { ConversationProvider } from "./lib/conversation-context";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProfilePage } from "./pages/ProfilePage";
import { HistoryPage } from "./pages/HistoryPage";
import { AdminPage } from "./pages/AdminPage";
import { Toaster } from "./components/ui/sonner";

type AuthView = "login" | "register" | "admin";
type AppPage = "dashboard" | "profile" | "history";

function AppContent() {
  const { isAuthenticated } = useAuth();
  const [authView, setAuthView] = useState<AuthView>("login");
  const [currentPage, setCurrentPage] = useState<AppPage>("dashboard");

  if (!isAuthenticated) {
    return (
      <>
        {authView === "login" && (
          <LoginPage 
            onSwitchToRegister={() => setAuthView("register")}
            onSwitchToAdmin={() => setAuthView("admin")}
          />
        )}
        {authView === "register" && (
          <RegisterPage onSwitchToLogin={() => setAuthView("login")} />
        )}
        {authView === "admin" && (
          <AdminPage onBack={() => setAuthView("login")} />
        )}
      </>
    );
  }

  return (
    <ProfileProvider>
      <ConversationProvider>
        {currentPage === "dashboard" && (
          <DashboardPage onNavigate={setCurrentPage} />
        )}
        {currentPage === "profile" && (
          <ProfilePage onBack={() => setCurrentPage("dashboard")} />
        )}
        {currentPage === "history" && (
          <HistoryPage onBack={() => setCurrentPage("dashboard")} />
        )}
      </ConversationProvider>
    </ProfileProvider>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <div className="size-full">
        <AppContent />
        <Toaster />
      </div>
    </AuthProvider>
  );
}
