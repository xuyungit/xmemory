import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import ProjectList from '../components/projects/ProjectList';
import ProjectDetail from '../components/projects/ProjectDetail';

const { Content } = Layout;

const Projects: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '16px' }}>
        <Routes>
          <Route path="/" element={<ProjectList />} />
          <Route path="/:projectId" element={<ProjectDetail />} />
        </Routes>
      </Content>
    </Layout>
  );
};

export default Projects;