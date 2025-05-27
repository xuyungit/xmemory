import React, { useState, useEffect } from 'react';
import { Card, List, Typography, Spin, Empty, Button, Layout, Modal, Form, Input, message } from 'antd';
import { FolderOutlined, PlusOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { getProjects, Project, createProject } from '../../services/memoryService';
import { getUserID } from '../../utils/userStorage';

const { Content } = Layout;
const { Paragraph } = Typography;
const { TextArea } = Input;

const ProjectList: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [form] = Form.useForm();
  
  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async (pageNum = 1) => {
    try {
      setLoading(true);
      const userId = getUserID();
      
      if (!userId) {
        console.error('用户未登录');
        return;
      }
      
      const response = await getProjects(userId, pageNum, 10, 'created_at', 'desc');
      
      if (pageNum === 1) {
        setProjects(response.memories as Project[]);
      } else {
        setProjects(prev => [...prev, ...(response.memories as Project[])]);
      }
      
      setPage(pageNum);
      setHasMore(response.page < response.total_pages);
    } catch (error) {
      console.error('获取项目列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMoreProjects = () => {
    if (!loading && hasMore) {
      fetchProjects(page + 1);
    }
  };

  const showCreateModal = () => {
    form.resetFields();
    setCreateModalVisible(true);
  };

  const handleCreateProject = async (values: { title: string; content: string }) => {
    try {
      setCreateLoading(true);
      
      // 调用创建项目API
      const newProject = await createProject(
        values.title,
        values.content,
        [] // 暂时不支持标签
      );
      
      // 确保新项目对象具有正确的结构和ID字段，以便在列表中正确显示
      const normalizedProject: Project = {
        ...newProject,
        id: newProject.id || newProject._id || '',  // 确保id字段存在
        _id: newProject._id || newProject.id || '',  // 确保_id字段存在
        title: values.title,  // 使用表单中的标题
        content: values.content,  // 使用表单中的内容
        created_at: newProject.created_at || new Date().toISOString()  // 确保created_at字段有效
      };
      
      // 更新项目列表
      setProjects(prev => [normalizedProject, ...prev]);
      setCreateModalVisible(false);
      message.success('项目创建成功');
    } catch (error) {
      console.error('创建项目失败:', error);
      message.error('创建项目失败');
    } finally {
      setCreateLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={showCreateModal}
        >
          新建项目
        </Button>
      </div>
      
      {loading && projects.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </div>
      ) : projects.length === 0 ? (
        <Empty description="暂无项目" />
      ) : (
        <List
          grid={{
            gutter: 16,
            xs: 1,
            sm: 1,
            md: 2,
            lg: 3,
            xl: 3,
            xxl: 3,
          }}
          dataSource={projects}
          renderItem={(project) => (
            <List.Item>
              <Link to={`/projects/${project.id || project._id}`} style={{ display: 'block', width: '100%' }}>
                <Card 
                  hoverable
                  title={
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <FolderOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                      {project.title || '未命名项目'}
                    </div>
                  }
                >
                  <Paragraph 
                    ellipsis={{ rows: 3, expandable: false }} 
                    style={{ 
                      marginBottom: 0,
                      wordBreak: 'break-word',
                      overflowWrap: 'break-word'
                    }}
                  >
                    {project.content}
                  </Paragraph>
                  <div style={{ marginTop: 16, fontSize: '12px', color: '#999' }}>
                    创建于: {new Date(project.created_at).toLocaleDateString()}
                  </div>
                </Card>
              </Link>
            </List.Item>
          )}
          loadMore={
            hasMore ? (
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <Button onClick={loadMoreProjects} loading={loading}>
                  加载更多
                </Button>
              </div>
            ) : null
          }
        />
      )}

      {/* 创建项目模态框 */}
      <Modal
        title="创建新项目"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateProject}
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
                onClick={() => setCreateModalVisible(false)}
              >
                取消
              </Button>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={createLoading}
              >
                创建
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProjectList;