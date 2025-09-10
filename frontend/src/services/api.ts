import axios, { AxiosInstance, AxiosResponse } from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

// TypeScript interfaces
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'student' | 'instructor' | 'admin';
  profile_picture?: string;
  date_joined: string;
}

export interface Course {
  id: string;
  title: string;
  code: string;
  description: string;
  instructor: User;
  semester: string;
  status: 'active' | 'inactive' | 'completed';
  enrolled_count: number;
  created_at: string;
}

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Track if we're currently refreshing token to avoid multiple requests
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

const subscribeTokenRefresh = (callback: (token: string) => void) => {
  refreshSubscribers.push(callback);
};

const onRefreshed = (token: string) => {
  refreshSubscribers.map(callback => callback(token));
  refreshSubscribers = [];
};

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, wait for the new token
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(apiClient(originalRequest));
          });
        });
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
      
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          localStorage.setItem('accessToken', access);
          onRefreshed(access);
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          // Refresh failed, logout user
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('userData');
          window.location.href = '/login';
        } finally {
          isRefreshing = false;
        }
      } else {
        // No refresh token, logout user
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('userData');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Helper function to handle API errors
export const handleApiError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  
  if (error.response?.data) {
    const firstError = Object.values(error.response.data)[0];
    if (Array.isArray(firstError)) {
      return firstError[0];
    }
    return String(firstError);
  }
  
  if (error.message) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
};

// API Service class
class ApiService {
  // Authentication endpoints
  auth = {
    login: async (email: string, password: string) => {
      const response = await apiClient.post('/auth/login/', { username: email, password });
      return response.data;
    },
    
    register: async (userData: {
      firstName: string;
      lastName: string;
      email: string;
      password: string;
    }) => {
      const response = await apiClient.post('/auth/register/', {
        first_name: userData.firstName,
        last_name: userData.lastName,
        email: userData.email,
        password: userData.password,
      });
      return response.data;
    },
    
    logout: async () => {
      await apiClient.post('/auth/logout/');
    },
    
    refreshToken: async (refresh: string) => {
      const response = await apiClient.post('/auth/refresh/', { refresh });
      return response.data;
    },
    
    profile: async () => {
      const response = await apiClient.get('/auth/profile/');
      return response.data;
    },
  };

  // Course endpoints
  courses = {
    list: async (params?: { semester?: string; status?: string; search?: string }) => {
      const response = await apiClient.get('/courses/', { params });
      return response.data;
    },
    
    get: async (id: string) => {
      const response = await apiClient.get(`/courses/${id}/`);
      return response.data;
    },
    
    enroll: async (courseId: string) => {
      const response = await apiClient.post(`/courses/${courseId}/enroll/`);
      return response.data;
    },
    
    unenroll: async (courseId: string) => {
      const response = await apiClient.post(`/courses/${courseId}/unenroll/`);
      return response.data;
    },
  };

  // Assessment endpoints
  assessments = {
    list: async (courseId?: string) => {
      const params = courseId ? { course: courseId } : {};
      const response = await apiClient.get('/assessments/', { params });
      return response.data;
    },
    
    get: async (id: string) => {
      const response = await apiClient.get(`/assessments/${id}/`);
      return response.data;
    },
    
    submit: async (id: string, answers: any) => {
      const response = await apiClient.post(`/assessments/${id}/submit/`, { answers });
      return response.data;
    },
  };

  // Message endpoints
  messages = {
    list: async (params?: { course?: string; unread?: boolean }) => {
      const response = await apiClient.get('/messages/', { params });
      return response.data;
    },
    
    get: async (id: string) => {
      const response = await apiClient.get(`/messages/${id}/`);
      return response.data;
    },
    
    send: async (data: {
      recipient: string;
      subject: string;
      content: string;
      course?: string;
    }) => {
      const response = await apiClient.post('/messages/', data);
      return response.data;
    },
    
    markAsRead: async (id: string) => {
      const response = await apiClient.patch(`/messages/${id}/`, { is_read: true });
      return response.data;
    },
  };

  // Analytics endpoints
  analytics = {
    dashboard: async () => {
      const response = await apiClient.get('/analytics/dashboard/');
      return response.data;
    },
    
    course: async (courseId: string) => {
      const response = await apiClient.get(`/analytics/courses/${courseId}/`);
      return response.data;
    },
    
    progress: async () => {
      const response = await apiClient.get('/analytics/progress/');
      return response.data;
    },
  };

  // Search endpoints
  search = {
    query: async (q: string, filters?: { type?: string; course?: string }) => {
      const params = { q, ...filters };
      const response = await apiClient.get('/search/', { params });
      return response.data;
    },
    
    suggestions: async (q: string) => {
      const response = await apiClient.get('/search/suggestions/', { params: { q } });
      return response.data;
    },
  };

  // File upload endpoints
  files = {
    upload: async (file: File, data?: { course?: string; assignment?: string }) => {
      const formData = new FormData();
      formData.append('file', file);
      if (data) {
        Object.entries(data).forEach(([key, value]) => {
          if (value) formData.append(key, value);
        });
      }
      
      const response = await apiClient.post('/files/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
    
    delete: async (id: string) => {
      await apiClient.delete(`/files/${id}/`);
    },
  };
}

// Export singleton instance
export const api = new ApiService();
export default apiClient;
