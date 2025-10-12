/**
 * Toast notifications with logging
 * Wraps sonner toast to log all user-facing messages
 */

import { toast as sonnerToast } from 'sonner';
import { logger } from './logger';

export const toast = {
  success: (message: string, data?: any) => {
    logger.info('toast', `✅ Success: ${message}`, data);
    return sonnerToast.success(message, data);
  },

  error: (message: string, data?: any) => {
    logger.error('toast', `❌ Error: ${message}`, data);
    return sonnerToast.error(message, data);
  },

  warning: (message: string, data?: any) => {
    logger.warn('toast', `⚠️ Warning: ${message}`, data);
    return sonnerToast.warning(message, data);
  },

  info: (message: string, data?: any) => {
    logger.info('toast', `ℹ️ Info: ${message}`, data);
    return sonnerToast.info(message, data);
  },

  loading: (message: string, data?: any) => {
    logger.info('toast', `⏳ Loading: ${message}`, data);
    return sonnerToast.loading(message, data);
  },

  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: any) => string);
    }
  ) => {
    logger.info('toast', `⏳ Promise started: ${messages.loading}`);
    
    return sonnerToast.promise(promise, {
      loading: messages.loading,
      success: (data) => {
        const msg = typeof messages.success === 'function' ? messages.success(data) : messages.success;
        logger.info('toast', `✅ Promise success: ${msg}`, data);
        return msg;
      },
      error: (error) => {
        const msg = typeof messages.error === 'function' ? messages.error(error) : messages.error;
        logger.error('toast', `❌ Promise error: ${msg}`, error);
        return msg;
      },
    });
  },
};

