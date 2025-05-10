import axios from 'axios';
import { setUserID } from '../utils/userStorage';
import { createApiInstance } from './apiService';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api/v1';

// 创建专用于认证的API实例
const authApi = createApiInstance({
  // 不在此处添加特别的配置，因为基础配置已经在createApiInstance中完成
});

// 特殊处理登录流程，因为它不需要添加Authorization头
export const login = async (username: string, password: string) => {
  // 使用普通的axios调用登录接口
  const response = await axios.post(`${API_BASE_URL}/auth/login`, {
    username,
    password,
  });
  
  if (response.data.session_id) {
    localStorage.setItem('session_id', response.data.session_id);
    setUserID(username);
    return response.data;
  }
  throw new Error('Login failed');
};

export const logout = async () => {
  try {
    const sessionId = getSessionId();
    if (sessionId) {
      await authApi.post(`/auth/logout`);
    }
  } catch (error) {
    console.error('Logout failed:', error);
  } finally {
    localStorage.removeItem('session_id');
  }
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('session_id');
};

export const getSessionId = () => {
  return localStorage.getItem('session_id');
};