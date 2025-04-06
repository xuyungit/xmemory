import React from 'react';
import { Layout } from 'antd';
import MemoryList from '../components/MemoryList';
import AppHeader from '../components/common/AppHeader';

const { Content } = Layout;

const Memories: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader title="记忆管理" />
      <Content style={{ padding: '16px' }}>
        <MemoryList />
      </Content>
    </Layout>
  );
};

export default Memories;