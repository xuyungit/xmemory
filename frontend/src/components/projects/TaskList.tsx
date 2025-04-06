import React, { useState, useEffect } from 'react';
import { List, Card, Tag, Button, Tooltip, Modal, Form, Input, Select, message, Empty, Spin } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getProjectTasks, Task, deleteMemory } from '../../services/memoryService';
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

const TaskList: React.FC<TaskListProps> = ({ projectId }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [deleteConfirmVisible, setDeleteConfirmVisible] = useState(false);
  const [deletingTaskId, setDeletingTaskId] = useState<string | null>(null);
  const [form] = Form.useForm();
  
  useEffect(() => {
    if (projectId) {
      fetchTasks();
    }
  }, [projectId]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const tasks = await getProjectTasks(projectId);
      
      // 按状态排序：To Do -> In Progress -> Done -> Deleted
      const sortOrder: Record<string, number> = {
        'To Do': 0,
        'In Progress': 1,
        'Done': 2,
        'Deleted': 3,
        '': 4 // 未设置状态的排最后
      };
      
      const sortedTasks = [...tasks].sort((a, b) => {
        const statusA = a.summary || '';
        const statusB = b.summary || '';
        return (sortOrder[statusA] || 999) - (sortOrder[statusB] || 999);
      });
      
      setTasks(sortedTasks);
    } catch (error) {
      console.error('获取任务列表失败:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleEditTask = (task: Task) => {
    setCurrentTask(task);
    form.setFieldsValue({
      title: task.title,
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
  
  const handleEditFormFinish = (values: any) => {
    // TODO: 实现编辑任务的API调用
    console.log('编辑任务:', values);
    message.info('任务编辑功能尚未实现');
    setEditModalVisible(false);
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <Spin />
      </div>
    );
  }

  return (
    <div>
      {/* 任务列表 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3>任务列表</h3>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => message.info('新建任务功能尚未实现')} // TODO: 实现新建任务功能
        >
          新建任务
        </Button>
      </div>
      
      {tasks.length === 0 ? (
        <Empty description="暂无任务" />
      ) : (
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
          dataSource={tasks}
          renderItem={(task) => (
            <List.Item>
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
                  <div style={{ whiteSpace: 'pre-line' }}>{task.content}</div>
                </div>
                <div style={{ 
                  marginTop: 16, 
                  fontSize: '12px', 
                  color: '#999', 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center' 
                }}>
                  <span>创建于: {new Date(task.created_at).toLocaleDateString()}</span>
                  <span>
                    <Button
                      type="text"
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => handleEditTask(task)}
                      style={{ marginRight: '4px' }}
                    />
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => confirmDeleteTask(task.id || task._id || '')}
                    />
                  </span>
                </div>
              </Card>
            </List.Item>
          )}
        />
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
            name="title"
            label="任务标题"
            rules={[{ required: true, message: '请输入任务标题' }]}
          >
            <Input placeholder="请输入任务标题" />
          </Form.Item>
          
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