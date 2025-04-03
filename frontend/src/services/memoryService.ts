import axios from 'axios';
import { getSessionId } from './authService';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include session ID
api.interceptors.request.use((config) => {
  const sessionId = getSessionId();
  if (sessionId) {
    config.headers.Authorization = `Bearer ${sessionId}`;
  }
  return config;
});

export interface Memory {
  id: string;
  user_id: string;
  title?: string;
  content: string;
  created_at: string;
  memory_type: string;
  tags: string[];
}

export const createMemory = async (data: {
  user_id: string;
  title?: string;
  content: string;
  tags?: string[];
  created_at?: string;
}): Promise<Memory> => {
  const response = await api.post('/memories/', data);
  return response.data;
};

export const getMemories = async (user_id?: string): Promise<Memory[]> => {
  const response = await api.get('/memories/', {
    params: {
      user_id,
    },
  });
  return response.data.memories;
};

export const searchMemories = async (
  user_id: string,
  searchText: string
): Promise<Memory[]> => {
  const response = await api.get('/memories/search', {
    params: {
      user_id,
      query: searchText,
    },
  });
  return response.data.memories;
}; 