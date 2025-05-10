import React from 'react';
import { Layout, Typography } from 'antd';
import MemoryList from '../components/MemoryList';
import AppHeader from '../components/common/AppHeader';

const { Content } = Layout;
const { Title } = Typography;

const Memories: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader />
      <Content style={{ padding: '16px' }}>
        <Title level={2} style={{ textAlign: 'center', marginBottom: '24px' }}>记忆管理</Title>
        <MemoryList />
      </Content>
    </Layout>
  );
};

export default Memories;