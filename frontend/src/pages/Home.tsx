import React from 'react';
import { Layout, Typography } from 'antd';
import CreateMemory from '../components/CreateMemory';
import AppHeader from '../components/common/AppHeader';

const { Content } = Layout;
const { Title } = Typography;

const Home: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader />
      <Content style={{ padding: '16px', textAlign: 'center' }}>
        <Title level={2}>欢迎来到记忆管理系统</Title>
        <CreateMemory />
      </Content>
    </Layout>
  );
};

export default Home;