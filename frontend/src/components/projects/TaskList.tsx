import React, { useState, useEffect } from 'react';
import { List, Card, Tag, Button, Tooltip, Modal, Form, Input, Select, message, Empty, Spin, Tabs } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getProjectTasks, Task, deleteMemory, updateMemory, createTask } from '../../services/memoryService';
import { getUserID } from '../../utils/userStorage';

interface TaskListProps {
  projectId: string;
}

// 任务状态对应的颜色
const statusColors: Record<string, string> = {
  'To Do': 'default',
  'In Progress': 'processing',
  'Done': 'success',
  'Deleted': 'error',
};

// 任务卡片组件
interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, onEdit, onDelete }) => (
  <Card 
    bordered={true}
    style={{ width: '100%' }}
    bodyStyle={{ padding: '16px' }}
    actions={[]}
  >
    <div>
      {task.summary && (
        <Tag color={statusColors[task.summary] || 'default'} style={{ marginBottom: '8px' }}>
          {task.summary}
        </Tag>
      )}
      <div style={{ 
        whiteSpace: 'pre-line',
        wordBreak: 'break-word',
        overflowWrap: 'break-word',
        maxWidth: '100%',
        overflow: 'hidden'
      }}>{task.content}</div>
    </div>
    <div style={{ 
      marginTop: 16, 
      fontSize: '12px', 
      color: '#999', 
      display: 'flex', 
      justifyContent: 'space-between', 
      flexDirection: 'column',
      alignItems: 'flex-start'
    }}>
      <div style={{ marginBottom: '4px' }}>
        <span>创建于: {task.created_at ? new Date(task.created_at).toLocaleDateString() : '未知日期'}</span>
      </div>
      {task.updated_at && task.updated_at !== task.created_at && (
        <div style={{ marginBottom: '4px' }}>
          <span>更新于: {new Date(task.updated_at).toLocaleDateString()}</span>
        </div>
      )}
      <div style={{ alignSelf: 'flex-end' }}>
        <Button
          type="text"
          size="small"
          icon={<EditOutlined />}
          onClick={() => onEdit(task)}
          style={{ marginRight: '4px' }}
        />
        <Button
          type="text"
          size="small"
          danger
          icon={<DeleteOutlined />}
          onClick={() => onDelete(task.id || task._id || '')}
        />
      </div>
    </div>
  </Card>
);

const TaskList: React.FC<TaskListProps> = ({ projectId }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [deleteConfirmVisible, setDeleteConfirmVisible] = useState(false);
  const [deletingTaskId, setDeletingTaskId] = useState<string | null>(null);
  const [form] = Form.useForm();
  const [createForm] = Form.useForm();
  const [createLoading, setCreateLoading] = useState(false);
  
  useEffect(() => {
    if (projectId) {
      fetchTasks();
    }
  }, [projectId]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const tasks = await getProjectTasks(projectId);
      
      // 先按照更新时间从新到旧排序
      const sortedByTime = [...tasks].sort((a, b) => {
        // 优先使用updated_at，如果没有则使用created_at
        const timeA = a.updated_at ? new Date(a.updated_at).getTime() : 
                     (a.created_at ? new Date(a.created_at).getTime() : 0);
        const timeB = b.updated_at ? new Date(b.updated_at).getTime() : 
                     (b.created_at ? new Date(b.created_at).getTime() : 0);
        return timeB - timeA; // 从新到旧排序
      });
      
      setTasks(sortedByTime);
    } catch (error) {
      console.error('获取任务列表失败:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleEditTask = (task: Task) => {
    setCurrentTask(task);
    form.setFieldsValue({
      content: task.content,
      status: task.summary || 'To Do'
    });
    setEditModalVisible(true);
  };
  
  const handleDeleteTask = async () => {
    if (!deletingTaskId) return;
    
    try {
      await deleteMemory(deletingTaskId);
      message.success('任务已删除');
      setTasks(tasks.filter(task => (task.id || task._id) !== deletingTaskId));
    } catch (error) {
      console.error('删除任务失败:', error);
      message.error('删除任务失败');
    } finally {
      setDeleteConfirmVisible(false);
      setDeletingTaskId(null);
    }
  };
  
  const confirmDeleteTask = (taskId: string) => {
    setDeletingTaskId(taskId);
    setDeleteConfirmVisible(true);
  };
  
  const handleEditFormFinish = async (values: any) => {
    if (!currentTask) return;
    
    try {
      const taskId = currentTask.id || currentTask._id || '';
      
      // 调用updateMemory API更新任务内容和状态（移除不在接口中的updated_at字段）
      await updateMemory(taskId, {
        content: values.content,
        summary: values.status
      });
      
      // 更新本地任务列表中的任务
      const updatedTask = {
        ...currentTask,
        content: values.content,
        summary: values.status,
        updated_at: new Date().toISOString() // 仅在前端状态中添加更新时间
      };
      
      // 使用map更新任务，然后按照更新时间重新排序
      const updatedTasks = tasks
        .map(task => ((task.id || task._id) === taskId ? updatedTask : task))
        .sort((a, b) => {
          // 优先使用updated_at，如果没有则使用created_at
          const timeA = a.updated_at ? new Date(a.updated_at).getTime() : 
                      (a.created_at ? new Date(a.created_at).getTime() : 0);
          const timeB = b.updated_at ? new Date(b.updated_at).getTime() : 
                      (b.created_at ? new Date(b.created_at).getTime() : 0);
          return timeB - timeA; // 从新到旧排序
        });
      
      setTasks(updatedTasks);
      message.success('任务更新成功');
      setEditModalVisible(false);
    } catch (error) {
      console.error('更新任务失败:', error);
      message.error('更新任务失败');
    }
  };

  const handleCreateTask = async (values: any) => {
    try {
      setCreateLoading(true);
      
      // 调用创建任务API
      const newTask = await createTask(
        projectId,
        values.content,
        values.status || 'To Do',
        []  // 暂时不支持添加标签
      );
      
      // 为新任务添加当前时间作为创建和更新时间
      const taskWithTimes = {
        ...newTask,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      // 将新任务添加到列表中，然后按照更新时间重新排序
      const updatedTasks = [...tasks, taskWithTimes].sort((a, b) => {
        // 优先使用updated_at，如果没有则使用created_at
        const timeA = a.updated_at ? new Date(a.updated_at).getTime() : 
                     (a.created_at ? new Date(a.created_at).getTime() : 0);
        const timeB = b.updated_at ? new Date(b.updated_at).getTime() : 
                     (b.created_at ? new Date(b.created_at).getTime() : 0);
        return timeB - timeA; // 从新到旧排序
      });
      
      setTasks(updatedTasks);
      message.success('任务创建成功');
      setCreateModalVisible(false);
      createForm.resetFields();
    } catch (error) {
      console.error('创建任务失败:', error);
      message.error('创建任务失败');
    } finally {
      setCreateLoading(false);
    }
  };
  
  const showCreateTaskModal = () => {
    createForm.resetFields(); // 重置表单字段
    setCreateModalVisible(true);
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <Spin />
      </div>
    );
  }

  // 根据状态过滤任务并渲染任务列表
  const renderTaskList = (status: string) => (
    <List
      grid={{
        gutter: 16,
        xs: 1,
        sm: 1,
        md: 1,
        lg: 2,
        xl: 2,
        xxl: 3,
      }}
      dataSource={tasks.filter(task => task.summary === status)}
      renderItem={(task) => (
        <List.Item>
          <TaskCard 
            task={task} 
            onEdit={handleEditTask} 
            onDelete={confirmDeleteTask}
          />
        </List.Item>
      )}
    />
  );

  return (
    <div>
      {/* 任务列表 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3>任务列表</h3>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={showCreateTaskModal}
        >
          新建任务
        </Button>
      </div>
      
      {tasks.length === 0 ? (
        <Empty description="暂无任务" />
      ) : (
        <Tabs defaultActiveKey="1">
          <Tabs.TabPane tab="进行中" key="1">
            {renderTaskList('In Progress')}
          </Tabs.TabPane>
          <Tabs.TabPane tab="待办" key="2">
            {renderTaskList('To Do')}
          </Tabs.TabPane>
          <Tabs.TabPane tab="已完成" key="3">
            {renderTaskList('Done')}
          </Tabs.TabPane>
        </Tabs>
      )}
      
      {/* 编辑任务对话框 */}
      <Modal
        title="编辑任务"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEditFormFinish}
        >
          <Form.Item
            name="content"
            label="任务内容"
            rules={[{ required: true, message: '请输入任务内容' }]}
          >
            <Input.TextArea rows={4} placeholder="请输入任务内容" />
          </Form.Item>
          
          <Form.Item
            name="status"
            label="任务状态"
            rules={[{ required: true, message: '请选择任务状态' }]}
          >
            <Select>
              <Select.Option value="To Do">待办</Select.Option>
              <Select.Option value="In Progress">进行中</Select.Option>
              <Select.Option value="Done">已完成</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item>
            <div style={{ textAlign: 'right' }}>
              <Button style={{ marginRight: 8 }} onClick={() => setEditModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 新建任务对话框 */}
      <Modal
        title="新建任务"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
        destroyOnClose
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreateTask}
        >
          <Form.Item
            name="content"
            label="任务内容"
            rules={[{ required: true, message: '请输入任务内容' }]}
          >
            <Input.TextArea rows={4} placeholder="请输入任务内容" />
          </Form.Item>
          
          <Form.Item
            name="status"
            label="任务状态"
            initialValue="To Do"
          >
            <Select>
              <Select.Option value="To Do">待办</Select.Option>
              <Select.Option value="In Progress">进行中</Select.Option>
              <Select.Option value="Done">已完成</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item>
            <div style={{ textAlign: 'right' }}>
              <Button style={{ marginRight: 8 }} onClick={() => setCreateModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={createLoading}>
                创建
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 删除确认对话框 */}
      <Modal
        title="确认删除"
        open={deleteConfirmVisible}
        onCancel={() => setDeleteConfirmVisible(false)}
        onOk={handleDeleteTask}
        okText="删除"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        <p>确定要删除这个任务吗？此操作不可恢复。</p>
      </Modal>
    </div>
  );
};

export default TaskList;