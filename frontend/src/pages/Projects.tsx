import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout, Typography } from 'antd';
import ProjectList from '../components/projects/ProjectList';
import ProjectDetail from '../components/projects/ProjectDetail';
import AppHeader from '../components/common/AppHeader';

const { Content } = Layout;
const { Title } = Typography;

const Projects: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader />
      <Content style={{ padding: '16px' }}>
        <Title level={2} style={{ textAlign: 'center', marginBottom: '24px' }}>项目管理</Title>
        <Routes>
          <Route path="/" element={<ProjectList />} />
          <Route path="/:projectId" element={<ProjectDetail />} />
        </Routes>
      </Content>
    </Layout>
  );
};

export default Projects;