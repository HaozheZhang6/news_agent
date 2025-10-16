import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useAuth } from "./auth-context";
import { projectId } from "../utils/supabase/info";

interface Interests {
  [key: string]: boolean;
}

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

interface Settings {
  speechRate: number;
  interruptionSensitivity: number;
  voiceType: string;
}

interface Notifications {
  marketAlerts: boolean;
  newsDigest: boolean;
  watchlistUpdates: boolean;
  dailyBrief: boolean;
}

interface Profile {
  interests: Interests;
  watchlist: Stock[];
  settings: Settings;
  notifications: Notifications;
}

interface ProfileContextType {
  profile: Profile | null;
  updateProfile: (updates: Partial<Profile>) => Promise<void>;
  isLoading: boolean;
}

const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

const defaultProfile: Profile = {
  interests: {},
  watchlist: [],
  settings: {
    speechRate: 1.0,
    interruptionSensitivity: 50,
    voiceType: 'professional'
  },
  notifications: {
    marketAlerts: true,
    newsDigest: true,
    watchlistUpdates: true,
    dailyBrief: false
  }
};

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { accessToken, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated && accessToken) {
      fetchProfile();
    } else {
      setProfile(null);
      setIsLoading(false);
    }
  }, [isAuthenticated, accessToken]);

  const fetchProfile = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-19e78e3b/profile`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setProfile({ ...defaultProfile, ...data.profile });
      } else {
        setProfile(defaultProfile);
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      setProfile(defaultProfile);
    } finally {
      setIsLoading(false);
    }
  };

  const updateProfile = async (updates: Partial<Profile>) => {
    try {
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-19e78e3b/profile`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
          body: JSON.stringify(updates),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setProfile(data.profile);
      } else {
        throw new Error('Failed to update profile');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      throw error;
    }
  };

  return (
    <ProfileContext.Provider value={{ profile, updateProfile, isLoading }}>
      {children}
    </ProfileContext.Provider>
  );
}

export function useProfile() {
  const context = useContext(ProfileContext);
  if (context === undefined) {
    throw new Error("useProfile must be used within a ProfileProvider");
  }
  return context;
}
