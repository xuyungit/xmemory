import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api/v1';

// 获取会话ID的函数，避免循环依赖
const getSessionId = () => {
  return localStorage.getItem('session_id');
};

// 创建并配置通用的axios实例
export const createApiInstance = (config?: AxiosRequestConfig): AxiosInstance => {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
    ...config,
  });

  // 请求拦截器 - 添加认证token
  instance.interceptors.request.use(
    (config) => {
      // 为接口添加token，登录接口除外
      if (!config.url?.includes('/auth/login')) {
        const sessionId = getSessionId();
        if (sessionId) {
          config.headers['Authorization'] = `Bearer ${sessionId}`;
        }
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // 响应拦截器 - 处理会话过期情况
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      return response;
    },
    (error) => {
      // 对于登录接口，不需要处理401错误
      if (error.config.url && !error.config.url.includes('/auth/login')) {
        // 如果响应状态码为401，则表示会话已过期或无效
        if (error.response && error.response.status === 401) {
          console.log('会话已过期或无效，正在登出...');
          
          // 避免循环依赖，直接执行登出操作
          localStorage.removeItem('session_id');
          
          // 重定向到登录页面
          window.location.href = '/login';
          return Promise.reject(new Error('会话已过期，请重新登录'));
        }
      }
      return Promise.reject(error);
    }
  );

  return instance;
};

// 导出默认API实例
export const api = createApiInstance();
