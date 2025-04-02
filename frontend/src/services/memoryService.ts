import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface Memory {
  id: string;
  user_id: string;
  title?: string;
  content: string;
  created_at: string;
}

export const createMemory = async (data: {
  user_id: string;
  title?: string;
  content: string;
}): Promise<Memory> => {
  const response = await axios.post(`${API_BASE_URL}/memories`, data);
  return response.data;
};

export const getMemories = async (user_id?: string): Promise<Memory[]> => {
  const response = await axios.get(`${API_BASE_URL}/memories`, {
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
  const response = await axios.get(`${API_BASE_URL}/memories/search`, {
    params: {
      user_id,
      query: searchText,
    },
  });
  return response.data.memories;
}; 