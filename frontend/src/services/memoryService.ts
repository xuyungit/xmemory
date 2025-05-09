import { api } from './apiService';
import { getUserID } from '../utils/userStorage';

export interface Memory {
  id: string;
  user_id: string;
  title?: string;
  content: string;
  created_at: string;
  updated_at?: string; // 添加updated_at字段
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

export interface Project extends Memory {
  // 项目特有属性，记忆类型为 project
  // 项目名称即为 title，项目描述即为 content
}

export interface Task extends Memory {
  // 任务特有属性，记忆类型为 task
  parent_id: string; // 所属项目ID
  summary?: string; // 任务状态
}

export const createMemory = async (data: {
  user_id: string;
  title?: string;
  content: string;
  tags?: string[];
  created_at?: string;
  memory_type?: string;
}): Promise<Memory> => {
  const response = await api.post('/memories/', {
    ...data,
    memory_type: data.memory_type || 'raw',
  });
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

export interface MemoryUpdateData {
  content?: string;
  tags?: string[];
  title?: string;
  summary?: string;
  parent_id?: string;
  related_ids?: string[];
}

export const updateMemory = async (
  memoryId: string,
  updateData: MemoryUpdateData,
  userId?: string
): Promise<Memory> => {
  // 使用当前登录的用户ID，如果没有提供特定的用户ID
  const currentUserId = userId || getUserID();
  const response = await api.put(`/memories/${memoryId}`, updateData, {
    params: {
      user_id: currentUserId,
    },
  });
  return response.data;
};

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

// 新增项目管理相关API

/**
 * 获取项目列表
 * 通过筛选 memory_type=project 的记忆来获取
 */
export const getProjects = async (
  user_id?: string,
  page: number = 1,
  pageSize: number = 20,
  sortBy: string = 'created_at',
  sortOrder: string = 'desc'
): Promise<PaginatedResponse> => {
  return await getMemories(
    user_id,
    page,
    pageSize,
    sortBy,
    sortOrder,
    'project'
  );
};

/**
 * 获取项目详情
 * @param projectId 项目ID
 */
export const getProjectDetail = async (projectId: string): Promise<Project | null> => {
  try {
    const repo = await api.get(`/memories/${projectId}`);
    return repo.data as Project;
  } catch (error) {
    console.error('获取项目详情失败:', error);
    return null;
  }
};

/**
 * 获取项目的任务列表
 * 通过筛选 memory_type=task 且 parent_id=项目ID 的记忆来获取
 * @param projectId 项目ID
 * @param user_id 用户ID
 */
export const getProjectTasks = async (
  projectId: string,
  user_id?: string
): Promise<Task[]> => {
  try {
    // 获取当前用户ID
    const currentUserId = user_id || getUserID();
    if (!currentUserId) {
      throw new Error('用户未登录');
    }
    
    // 使用API查询与项目相关的任务
    const response = await api.get('/memories/', {
      params: {
        user_id: currentUserId,
        memory_type: 'task',
        parent_id: projectId,
        page_size: 100,
      },
    });
    
    // 返回任务列表
    return response.data.memories as Task[];
  } catch (error) {
    console.error('获取项目任务失败:', error);
    return [];
  }
};

/**
 * 创建新项目
 * @param title 项目名称
 * @param content 项目描述
 * @param tags 项目标签
 * @returns 创建的项目对象
 */
export const createProject = async (
  title: string,
  content: string,
  tags: string[] = []
): Promise<Project> => {
  const userId = getUserID();
  if (!userId) {
    throw new Error('用户未登录');
  }
  
  const projectData = {
    user_id: userId,
    title,
    content,
    tags,
    memory_type: 'project',
  };
  
  const response = await createMemory(projectData);
  return response as Project;
};

/**
 * 创建新任务
 * @param projectId 项目ID
 * @param taskDescription 任务描述
 * @param status 任务状态（可选，默认为"To Do"）
 * @param tags 任务标签（可选）
 * @returns 创建的任务对象
 */
export const createTask = async (
  projectId: string,
  taskDescription: string,
  status: string = 'To Do',
  tags: string[] = []
): Promise<Task> => {
  const userId = getUserID();
  if (!userId) {
    throw new Error('用户未登录');
  }
  
  const taskData = {
    user_id: userId,
    title: taskDescription,
    content: taskDescription,
    tags,
    memory_type: 'task',
    parent_id: projectId,
    summary: status,
  };
  
  const response = await createMemory(taskData);

  // 确保返回完整的任务对象
  const createdTask: Task = {
    ...response,
    parent_id: projectId,
    content: taskDescription, // 确保内容字段正确
    summary: status,          // 确保状态字段正确
    // 如果日期格式有问题，可以尝试标准化日期格式
    created_at: response.created_at || new Date().toISOString()
  };
  
  console.log('创建的任务对象：', createdTask);
  return createdTask;
};
