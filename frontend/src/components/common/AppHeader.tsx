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
      padding: '0 10px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
      height: 'auto',
      position: 'sticky',
      top: 0,
      zIndex: 1000
    }}>
      {/* 中间标题 */}
      {title && (
        <Title level={4} style={{ margin: '8px 0', textAlign: 'center' }}>
          {title}
        </Title>
      )}

      {/* 导航菜单 - 移动端优化 */}
      <div style={{ 
        width: '100%', 
        display: 'flex', 
        flexWrap: 'nowrap', 
        overflowX: 'auto',
        paddingBottom: '8px',
        margin: '0 -5px',
        WebkitOverflowScrolling: 'touch',
        scrollbarWidth: 'none',
        msOverflowStyle: 'none'
      }}>
        <style>{`
          /* 隐藏滚动条但保留功能 */
          div::-webkit-scrollbar {
            display: none;
          }
        `}</style>
        
        <Button 
          icon={<HomeOutlined />} 
          type={getCurrentPath() === 'home' ? 'primary' : 'default'}
          onClick={() => navigate('/')}
          style={{ margin: '0 5px', flex: '0 0 auto', whiteSpace: 'nowrap' }}
          size="middle"
        >
          首页
        </Button>
        <Button 
          icon={<UnorderedListOutlined />} 
          type={getCurrentPath() === 'memories' ? 'primary' : 'default'}
          onClick={() => navigate('/memories')}
          style={{ margin: '0 5px', flex: '0 0 auto', whiteSpace: 'nowrap' }}
          size="middle"
        >
          记忆管理
        </Button>
        <Button 
          icon={<SearchOutlined />} 
          type={getCurrentPath() === 'search' ? 'primary' : 'default'}
          onClick={() => navigate('/search')}
          style={{ margin: '0 5px', flex: '0 0 auto', whiteSpace: 'nowrap' }}
          size="middle"
        >
          记忆搜索
        </Button>
        <Button 
          icon={<ProjectOutlined />} 
          type={getCurrentPath() === 'projects' ? 'primary' : 'default'}
          onClick={() => navigate('/projects')}
          style={{ margin: '0 5px', flex: '0 0 auto', whiteSpace: 'nowrap' }}
          size="middle"
        >
          项目管理
        </Button>
      </div>
      
      {/* 右侧登出按钮 */}
      <Button 
        type="text" 
        icon={<LogoutOutlined />} 
        onClick={handleLogout}
        style={{ position: 'absolute', right: '10px', top: title ? '8px' : '50%', transform: title ? 'none' : 'translateY(-50%)' }}
        size="middle"
      >
        退出登录
      </Button>
    </Header>
  );
};

export default AppHeader;