import React, { useState } from 'react';
import { Tabs, Layout } from 'antd';
import CreateMemory from '../components/CreateMemory';
import MemoryList from '../components/MemoryList';
import SearchMemory from '../components/SearchMemory';

const { Content } = Layout;

const Home: React.FC = () => {
  const [activeTab, setActiveTab] = useState('1');

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
      <Content style={{ padding: '24px' }}>
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