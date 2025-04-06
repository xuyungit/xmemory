import React, { useState } from 'react';
import { Tabs, Layout, Button, Space } from 'antd';
import { LogoutOutlined, ProjectOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import CreateMemory from '../components/CreateMemory';
import MemoryList from '../components/MemoryList';
import SearchMemory from '../components/SearchMemory';
import { logout } from '../services/authService';

const { Content, Header } = Layout;

const Home: React.FC = () => {
  const [activeTab, setActiveTab] = useState('1');
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const items = [
    {
      key: '1',
      label: '记录记忆',
      children: <CreateMemory />,
    },
    {
      key: '2',
      label: '记忆列表',
      children: <MemoryList />,
    },
    {
      key: '3',
      label: '查找记忆',
      children: <SearchMemory />,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
        height: '48px',
        lineHeight: '48px'
      }}>
        <div>
          <Button 
            type="primary" 
            icon={<ProjectOutlined />} 
            onClick={() => navigate('/projects')}
          >
            项目管理
          </Button>
        </div>
        <Button 
          type="text" 
          icon={<LogoutOutlined />} 
          onClick={handleLogout}
          style={{ padding: '0 4px' }}
        >
          退出登录
        </Button>
      </Header>
      <Content style={{ padding: '16px' }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={items}
          centered
        />
      </Content>
    </Layout>
  );
};

export default Home;