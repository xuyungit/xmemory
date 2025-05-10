import React from 'react';
import { Layout, Typography } from 'antd';
import SearchMemory from '../components/SearchMemory';
import AppHeader from '../components/common/AppHeader';

const { Content } = Layout;
const { Title } = Typography;

const Search: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader />
      <Content style={{ padding: '16px' }}>
        <Title level={2} style={{ textAlign: 'center', marginBottom: '24px' }}>记忆搜索</Title>
        <SearchMemory />
      </Content>
    </Layout>
  );
};

export default Search;