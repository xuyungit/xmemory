import React from 'react';
import { Layout } from 'antd';
import SearchMemory from '../components/SearchMemory';
import AppHeader from '../components/common/AppHeader';

const { Content } = Layout;

const Search: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader title="记忆搜索" />
      <Content style={{ padding: '16px' }}>
        <SearchMemory />
      </Content>
    </Layout>
  );
};

export default Search;