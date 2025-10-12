/**
 * API Client with comprehensive logging
 * Wraps fetch calls and logs all HTTP requests/responses
 */

import { logger } from './logger';

const API_BASE_URL = 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
}

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    logger.info('api', `APIClient initialized with baseUrl: ${baseUrl}`);
  }

  private buildUrl(endpoint: string, params?: Record<string, string>): string {
    const url = new URL(endpoint, this.baseUrl);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }
    return url.toString();
  }

  async request<T = any>(
    method: string,
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { params, ...fetchOptions } = options;
    const url = this.buildUrl(endpoint, params);
    const startTime = Date.now();

    // Log request
    logger.info('api', `📤 HTTP ${method} ${endpoint}`, {
      url,
      params,
      body: fetchOptions.body ? JSON.parse(fetchOptions.body as string) : undefined
    });

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        method,
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers,
        },
      });

      const duration = Date.now() - startTime;
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        // Log error response
        logger.error('api', `❌ HTTP ${method} ${endpoint} failed`, {
          status: response.status,
          statusText: response.statusText,
          duration: `${duration}ms`,
          data
        });
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Log successful response
      logger.info('api', `📥 HTTP ${method} ${endpoint} success`, {
        status: response.status,
        duration: `${duration}ms`,
        dataSize: JSON.stringify(data).length
      });

      return data;
    } catch (error) {
      const duration = Date.now() - startTime;
      logger.error('api', `❌ HTTP ${method} ${endpoint} error`, {
        duration: `${duration}ms`,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  async get<T = any>(endpoint: string, params?: Record<string, string>): Promise<T> {
    return this.request<T>('GET', endpoint, { params });
  }

  async post<T = any>(endpoint: string, body?: any): Promise<T> {
    return this.request<T>('POST', endpoint, {
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async put<T = any>(endpoint: string, body?: any): Promise<T> {
    return this.request<T>('PUT', endpoint, {
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T = any>(endpoint: string): Promise<T> {
    return this.request<T>('DELETE', endpoint);
  }
}

// Singleton instance
export const apiClient = new APIClient();

// Convenience methods
export const api = {
  get: apiClient.get.bind(apiClient),
  post: apiClient.post.bind(apiClient),
  put: apiClient.put.bind(apiClient),
  delete: apiClient.delete.bind(apiClient),
};

