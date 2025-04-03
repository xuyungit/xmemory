import axios from 'axios';
import { setUserID } from '../utils/userStorage';

const API_BASE_URL = '/api/v1';

export const login = async (username: string, password: string) => {
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
      await axios.post(`${API_BASE_URL}/auth/logout`, null, {
        headers: {
          'Authorization': `Bearer ${sessionId}`
        }
      });
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