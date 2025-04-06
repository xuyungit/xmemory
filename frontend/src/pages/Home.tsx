import React, { useState } from 'react';
import { Tabs, Layout } from 'antd';
import { useNavigate } from 'react-router-dom';
import CreateMemory from '../components/CreateMemory';
import MemoryList from '../components/MemoryList';
import SearchMemory from '../components/SearchMemory';
import AppHeader from '../components/common/AppHeader';

const { Content } = Layout;

const Home: React.FC = () => {
  const [activeTab, setActiveTab] = useState('1');
  const navigate = useNavigate();

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
      <AppHeader title="记忆管理" />
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