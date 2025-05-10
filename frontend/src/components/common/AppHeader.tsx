import React from 'react';
import { Layout, Button, Menu } from 'antd';
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

const AppHeader: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // 从路径中确定当前活动菜单项
  const getCurrentPath = () => {
    const path = location.pathname;
    if (path === '/') return 'home';
    if (path.startsWith('/memories')) return 'memories';
    if (path.startsWith('/search')) return 'search';
    if (path.startsWith('/projects')) return 'projects';
    return '';
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Determine dynamic button texts
  let memoriesButtonText = "记忆管理";
  if (location.pathname === '/memories/add' || location.pathname === '/memories/new') {
    memoriesButtonText = "创建记忆";
  } else if (location.pathname.startsWith('/memories/edit/')) {
    memoriesButtonText = "编辑记忆";
  }

  let projectsButtonText = "项目管理";
  if (location.pathname === '/projects/add' || location.pathname === '/projects/new') {
    projectsButtonText = "创建项目";
  } else if (location.pathname.startsWith('/projects/edit/')) {
    projectsButtonText = "编辑项目";
  }

  return (
    <Header style={{ 
      background: '#fff', 
      padding: '10px 10px', // Vertical and horizontal padding
      display: 'flex',
      alignItems: 'center', // Vertically align all items in the header
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
      height: 'auto', // Or a fixed height like 56px or 64px if preferred
      position: 'sticky',
      top: 0,
      zIndex: 1000
    }}>
      {/* Scrollable Navigation Menu */}
      <div style={{ 
        display: 'flex', 
        flexWrap: 'nowrap', // Ensure buttons stay in a line
        overflowX: 'auto',
        flexShrink: 0, // Prevent nav container from shrinking; content will scroll
        WebkitOverflowScrolling: 'touch',
        scrollbarWidth: 'none', // Hide scrollbar for Firefox
        msOverflowStyle: 'none'  // Hide scrollbar for IE/Edge
      }}>
        <style>{`
          /* Hide scrollbar for Webkit browsers */
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
          {memoriesButtonText}
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
          {projectsButtonText}
        </Button>
      </div>

      {/* Spacer to push logout button to the right */}
      <div style={{ flexGrow: 1 }} />
      
      {/* Logout Button */}
      <Button 
        type="text" 
        icon={<LogoutOutlined />} 
        onClick={handleLogout}
        style={{ 
          flexShrink: 0 // Prevent logout button from shrinking
        }}
        size="middle"
      >
        退出登录
      </Button>
    </Header>
  );
};

export default AppHeader;