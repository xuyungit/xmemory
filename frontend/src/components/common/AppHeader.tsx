import React from 'react';
import { Layout, Button, Space, Menu, Typography } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  HomeOutlined, 
  UnorderedListOutlined, 
  SearchOutlined, 
  ProjectOutlined, 
  LogoutOutlined 
} from '@ant-design/icons';
import { logout } from '../../services/authService';

const { Header } = Layout;
const { Title } = Typography;

interface AppHeaderProps {
  title?: string; // 可选标题，显示在中间
}

const AppHeader: React.FC<AppHeaderProps> = ({ title }) => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // 从路径中确定当前活动菜单项
  const getCurrentPath = () => {
    const path = location.pathname;
    if (path === '/') return 'home';
    if (path.includes('/memories')) return 'memories';
    if (path.includes('/search')) return 'search';
    if (path.includes('/projects')) return 'projects';
    return '';
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <Header style={{ 
      background: '#fff', 
      padding: '0 16px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
      height: '48px',
      lineHeight: '48px',
      position: 'sticky',
      top: 0,
      zIndex: 1000
    }}>
      {/* 左侧导航菜单 */}
      <Space wrap style={{ flexGrow: 1, display: 'flex', justifyContent: 'flex-start', overflow: 'auto' }}>
        <Button 
          icon={<HomeOutlined />} 
          type={getCurrentPath() === 'home' ? 'primary' : 'default'}
          onClick={() => navigate('/')}
        >
          首页
        </Button>
        <Button 
          icon={<UnorderedListOutlined />} 
          type={getCurrentPath() === 'memories' ? 'primary' : 'default'}
          onClick={() => navigate('/memories')}
        >
          记忆管理
        </Button>
        <Button 
          icon={<SearchOutlined />} 
          type={getCurrentPath() === 'search' ? 'primary' : 'default'}
          onClick={() => navigate('/search')}
        >
          记忆搜索
        </Button>
        <Button 
          icon={<ProjectOutlined />} 
          type={getCurrentPath() === 'projects' ? 'primary' : 'default'}
          onClick={() => navigate('/projects')}
        >
          项目管理
        </Button>
      </Space>

      {/* 中间标题 */}
      {title && (
        <Title level={4} style={{ margin: 0, textAlign: 'center', flexShrink: 0 }}>
          {title}
        </Title>
      )}
      
      {/* 右侧登出按钮 */}
      <Button 
        type="text" 
        icon={<LogoutOutlined />} 
        onClick={handleLogout}
        style={{ flexShrink: 0 }}
      >
        退出登录
      </Button>
    </Header>
  );
};

export default AppHeader;