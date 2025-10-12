import { useState, useEffect } from "react";
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
import { ErrorBoundary } from "./components/ErrorBoundary";
import { logger } from "./utils/logger";

type AuthView = "login" | "register" | "admin";
type AppPage = "dashboard" | "profile" | "history";

function AppContent() {
  const { isAuthenticated } = useAuth();
  const [authView, setAuthView] = useState<AuthView>("login");
  const [currentPage, setCurrentPage] = useState<AppPage>("dashboard");

  // Log navigation changes
  useEffect(() => {
    if (isAuthenticated) {
      logger.info('navigation', `Navigated to page: ${currentPage}`);
    } else {
      logger.info('navigation', `Viewing auth page: ${authView}`);
    }
  }, [currentPage, authView, isAuthenticated]);

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
  useEffect(() => {
    logger.info('app', 'Voice News Agent application started');
    logger.info('app', `Environment: ${import.meta.env.MODE || 'development'}`);
    logger.info('app', `User Agent: ${navigator.userAgent}`);

    // Global error handlers
    const handleError = (event: ErrorEvent) => {
      logger.error('app', 'Unhandled error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
      });
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      logger.error('app', 'Unhandled promise rejection', {
        reason: event.reason
      });
    };

    // Add listeners
    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    // Cleanup
    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      logger.info('app', 'Voice News Agent application shutting down');
    };
  }, []);

  return (
    <ErrorBoundary>
      <AuthProvider>
        <div className="size-full">
          <AppContent />
          <Toaster />
        </div>
      </AuthProvider>
    </ErrorBoundary>
  );
}
