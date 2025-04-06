import React, { useState, useEffect } from 'react';
import { Card, List, Typography, Spin, Empty, Button, Tooltip } from 'antd';
import { FolderOutlined, PlusOutlined, HomeOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { getProjects, Project } from '../../services/memoryService';
import { getUserID } from '../../utils/userStorage';

const { Title, Paragraph } = Typography;

const ProjectList: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const navigate = useNavigate();
  
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

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '0 16px' }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Button 
            icon={<HomeOutlined />} 
            onClick={() => navigate('/')}
            style={{ marginRight: 16 }}
          >
            返回主页
          </Button>
          <Title level={2} style={{ margin: 0 }}>项目列表</Title>
        </div>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={() => console.log('创建新项目')} // TODO: 创建新项目功能
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
                    style={{ marginBottom: 0 }}
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
    </div>
  );
};

export default ProjectList;