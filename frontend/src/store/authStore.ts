import { create } from 'zustand';
import { User } from '@/types';
import { apiClient } from '@/lib/api/client';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,

  login: async (email: string, password: string) => {
    try {
      set({ isLoading: true });
      const response = await apiClient.login(email, password);
      
      const { access_token, user } = response;
      
      apiClient.setToken(access_token);
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_user', JSON.stringify(user));
        localStorage.setItem('auth_token', access_token);
      }
      
      set({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  register: async (data: any) => {
    try {
      set({ isLoading: true });
      const response = await apiClient.register(data);
      
      if (response.access_token) {
        const { access_token, user } = response;
        apiClient.setToken(access_token);
        
        // Save to localStorage
        if (typeof window !== 'undefined') {
          localStorage.setItem('auth_user', JSON.stringify(user));
          localStorage.setItem('auth_token', access_token);
        }
        
        set({
          user,
          token: access_token,
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    apiClient.clearToken();
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_user');
      localStorage.removeItem('auth_token');
    }
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  },

  setUser: (user: User) => {
    set({ user });
  },

  checkAuth: async () => {
    try {
      const savedToken = typeof window !== 'undefined'
        ? localStorage.getItem('auth_token')
        : null;
      const savedUser = typeof window !== 'undefined'
        ? localStorage.getItem('auth_user')
        : null;
      
      if (!savedToken) {
        set({ isAuthenticated: false, user: null });
        return;
      }

      apiClient.setToken(savedToken);

      // If we have saved user, use it immediately
      if (savedUser) {
        try {
          const user = JSON.parse(savedUser);
          set({
            user,
            token: savedToken,
            isAuthenticated: true,
          });
        } catch (e) {
          // Invalid JSON, continue to fetch from API
        }
      }
    } catch (error) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_user');
        localStorage.removeItem('auth_token');
      }
      set({
        user: null,
        token: null,
        isAuthenticated: false,
      });
    }
  },
}));
