import React from 'react';
import { Layout } from 'antd';
import CreateMemory from '../components/CreateMemory';
import AppHeader from '../components/common/AppHeader';

const { Content } = Layout;

const Home: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader title="创建记忆" />
      <Content style={{ padding: '16px', display: 'flex', justifyContent: 'center' }}>
        <CreateMemory />
      </Content>
    </Layout>
  );
};

export default Home;