import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Typography, Card, Button, Space, Spin, Divider, message, Tooltip } from 'antd';
import { ArrowLeftOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getProjectDetail, deleteMemory, Project } from '../../services/memoryService';
import TaskList from './TaskList';

const { Title, Paragraph } = Typography;

const ProjectDetail: React.FC = () => {
  const { projectId = '' } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleteLoading, setDeleteLoading] = useState(false);

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

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!project) {
    return null;
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '0 16px' }}>
      {/* 返回按钮和操作栏 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/projects')}
        >
          返回项目列表
        </Button>
        
        <Space>
          <Tooltip title="编辑项目">
            <Button 
              icon={<EditOutlined />} 
              onClick={() => console.log('编辑项目')} // TODO: 实现编辑项目功能
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
    </div>
  );
};

export default ProjectDetail;