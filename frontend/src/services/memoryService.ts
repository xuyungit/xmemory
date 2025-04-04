import axios from 'axios';
import { getSessionId } from './authService';
import { getUserID } from '../utils/userStorage';

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
  _id?: string; // 添加_id字段，确保从后端返回的_id被保存
}

export interface PaginatedResponse {
  memories: Memory[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
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

export const getMemories = async (
  user_id?: string,
  page: number = 1,
  pageSize: number = 10,
  sortBy: string = 'created_at',
  sortOrder: string = 'desc',
  memory_type?: string
): Promise<PaginatedResponse> => {
  const response = await api.get('/memories/', {
    params: {
      user_id,
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
      memory_type,
    },
  });
  return response.data;
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

export interface DeleteMemoryResponse {
  success: boolean;
  message: string;
}

export const deleteMemory = async (
  memoryId: string, 
  userId?: string
): Promise<DeleteMemoryResponse> => {
  // 使用当前登录的用户ID，如果没有提供特定的用户ID
  const currentUserId = userId || getUserID();
  const response = await api.delete(`/memories/${memoryId}`, {
    params: {
      user_id: currentUserId,
    },
  });
  return response.data;
};