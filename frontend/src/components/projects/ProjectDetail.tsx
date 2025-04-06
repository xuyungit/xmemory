import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Typography, Card, Button, Space, Spin, Divider, message, Tooltip, Modal, Form, Input, Layout } from 'antd';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getProjectDetail, deleteMemory, Project, updateMemory } from '../../services/memoryService';
import TaskList from './TaskList';
import AppHeader from '../common/AppHeader';

const { Content } = Layout;
const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const ProjectDetail: React.FC = () => {
  const { projectId = '' } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [form] = Form.useForm();

  const fetchProjectDetail = useCallback(async () => {
    try {
      setLoading(true);
      if (!projectId) return;
      
      const projectData = await getProjectDetail(projectId);
      if (projectData) {
        setProject(projectData);
      } else {
        message.error('项目不存在或已被删除');
        navigate('/projects');
      }
    } catch (error) {
      console.error('获取项目详情失败:', error);
      message.error('获取项目详情失败');
    } finally {
      setLoading(false);
    }
  }, [projectId, navigate]);

  useEffect(() => {
    if (projectId) {
      fetchProjectDetail();
    }
  }, [projectId, fetchProjectDetail]);

  const handleDeleteProject = async () => {
    if (!projectId || !project) return;
    
    try {
      setDeleteLoading(true);
      await deleteMemory(projectId);
      message.success('项目已删除');
      navigate('/projects');
    } catch (error) {
      console.error('删除项目失败:', error);
      message.error('删除项目失败');
    } finally {
      setDeleteLoading(false);
    }
  };

  const showEditModal = () => {
    if (!project) return;
    
    // 初始化表单数据
    form.setFieldsValue({
      title: project.title || '',
      content: project.content || '',
    });
    
    setEditModalVisible(true);
  };

  const handleEditProject = async (values: { title: string; content: string }) => {
    if (!project || !projectId) return;
    
    try {
      setEditLoading(true);
      
      // 使用updateMemory方法更新项目
      const updatedProject = await updateMemory(projectId, {
        title: values.title,
        content: values.content,
      });
      
      setProject(updatedProject as Project);
      setEditModalVisible(false);
      message.success('项目更新成功');
    } catch (error) {
      console.error('更新项目失败:', error);
      message.error('更新项目失败');
    } finally {
      setEditLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <AppHeader title="项目详情" />
        <Content style={{ padding: '16px' }}>
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" />
          </div>
        </Content>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <AppHeader title="项目详情" />
        <Content style={{ padding: '16px' }}>
          <div style={{ textAlign: 'center', padding: '50px' }}>
            项目不存在
          </div>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader title={project.title || "项目详情"} />
      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          {/* 操作栏 */}
          <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
            <Space>
              <Tooltip title="编辑项目">
                <Button 
                  icon={<EditOutlined />} 
                  onClick={showEditModal}
                >
                  编辑
                </Button>
              </Tooltip>
              <Tooltip title="删除项目">
                <Button 
                  danger 
                  icon={<DeleteOutlined />} 
                  onClick={handleDeleteProject}
                  loading={deleteLoading}
                >
                  删除
                </Button>
              </Tooltip>
            </Space>
          </div>
          
          {/* 项目详情卡片 */}
          <Card>
            <Title level={2}>{project.title || '未命名项目'}</Title>
            <Paragraph style={{ whiteSpace: 'pre-line' }}>
              {project.content}
            </Paragraph>
            <div style={{ fontSize: '14px', color: '#666' }}>
              <div>创建于: {new Date(project.created_at).toLocaleString()}</div>
              {project.updated_at && project.updated_at !== project.created_at && (
                <div>更新于: {new Date(project.updated_at).toLocaleString()}</div>
              )}
            </div>
          </Card>
          
          {/* 项目任务列表 */}
          <Divider orientation="left">项目任务</Divider>
          <TaskList projectId={projectId} />

          {/* 编辑项目模态框 */}
          <Modal
            title="编辑项目"
            open={editModalVisible}
            onCancel={() => setEditModalVisible(false)}
            footer={null}
            destroyOnClose
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleEditProject}
            >
              <Form.Item
                name="title"
                label="项目名称"
                rules={[{ required: true, message: '请输入项目名称' }]}
              >
                <Input placeholder="请输入项目名称" />
              </Form.Item>
              
              <Form.Item
                name="content"
                label="项目描述"
                rules={[{ required: true, message: '请输入项目描述' }]}
              >
                <TextArea 
                  placeholder="请输入项目描述" 
                  autoSize={{ minRows: 4, maxRows: 8 }}
                />
              </Form.Item>
              
              <Form.Item>
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <Button 
                    style={{ marginRight: 8 }} 
                    onClick={() => setEditModalVisible(false)}
                  >
                    取消
                  </Button>
                  <Button 
                    type="primary" 
                    htmlType="submit"
                    loading={editLoading}
                  >
                    保存
                  </Button>
                </div>
              </Form.Item>
            </Form>
          </Modal>
        </div>
      </Content>
    </Layout>
  );
};

export default ProjectDetail;