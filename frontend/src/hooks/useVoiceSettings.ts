/**
 * Voice Settings Hook
 *
 * Manages voice settings with local storage persistence
 */

import { useState, useEffect, useCallback } from 'react';
import { VoiceSettings, DEFAULT_VOICE_SETTINGS } from '../types/voice-settings';

const STORAGE_KEY = 'voice_settings';

export function useVoiceSettings() {
  const [settings, setSettings] = useState<VoiceSettings>(DEFAULT_VOICE_SETTINGS);
  const [isLoading, setIsLoading] = useState(true);

  // Load settings from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setSettings({ ...DEFAULT_VOICE_SETTINGS, ...parsed });
      }
    } catch (error) {
      console.error('Failed to load voice settings:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save settings to localStorage
  const saveSettings = useCallback((newSettings: Partial<VoiceSettings>) => {
    setSettings((prev) => {
      const updated = { ...prev, ...newSettings };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (error) {
        console.error('Failed to save voice settings:', error);
      }
      return updated;
    });
  }, []);

  // Reset to defaults
  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_VOICE_SETTINGS);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('Failed to reset voice settings:', error);
    }
  }, []);

  // Update individual setting
  const updateSetting = useCallback(<K extends keyof VoiceSettings>(
    key: K,
    value: VoiceSettings[K]
  ) => {
    saveSettings({ [key]: value } as Partial<VoiceSettings>);
  }, [saveSettings]);

  return {
    settings,
    isLoading,
    saveSettings,
    resetSettings,
    updateSetting,
  };
}
