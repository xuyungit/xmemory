import React, { useState, useEffect } from 'react';
import { Form, Input, Button, List, Card, Typography, Spin, Empty } from 'antd';
import { useNavigate } from 'react-router-dom';
import { searchMemories } from '../services/memoryService';
import { getUserID } from '../utils/userStorage';

const { Title, Paragraph } = Typography;

interface Memory {
  id: string;
  user_id: string;
  title?: string;
  content: string;
  created_at: string;
}

const SearchMemory: React.FC = () => {
  const [form] = Form.useForm();
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { searchText: string }) => {
    try {
      setLoading(true);
      const user_id = getUserID();
      
      if (!user_id) {
        console.error('用户未登录');
        return;
      }
      
      const data = await searchMemories(user_id, values.searchText);
      setMemories(data);
    } catch (error) {
      console.error('搜索记忆失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      maxWidth: 800, 
      margin: '0 auto',
      padding: '0 16px' // 添加水平内边距，提高小屏幕设备的显示效果
    }}>
      <Title 
        level={3} 
        style={{ 
          textAlign: 'center', 
          marginBottom: 24,
          fontSize: 'calc(1.1rem + 0.5vw)' // 使用响应式字体大小
        }}
      >
        搜索您的记忆
      </Title>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        style={{ marginBottom: 24 }}
      >
        <Form.Item
          name="searchText"
          label="搜索内容"
          rules={[{ required: true, message: '请输入搜索内容' }]}
        >
          <Input placeholder="请输入要搜索的内容" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            搜索
          </Button>
        </Form.Item>
      </Form>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin size="large" />
        </div>
      ) : memories.length === 0 ? (
        <Empty description="未找到相关记忆" />
      ) : (
        <List
          grid={{ 
            gutter: 16, 
            xs: 1,        // 超小屏幕设备上一行显示1个
            sm: 1,        // 小屏幕设备上一行显示1个
            md: 2,        // 中等屏幕上一行显示2个
            lg: 3,        // 大屏幕上一行显示3个
            xl: 3,        // 超大屏幕上一行显示3个
            xxl: 3        // 超超大屏幕上一行显示3个
          }}
          dataSource={memories}
          renderItem={(memory) => (
            <List.Item>
              <Card
                title={memory.title || '无标题'}
                extra={<small>{memory.user_id}</small>}
                style={{ marginBottom: '16px' }} // 添加卡片间的垂直间距
              >
                <Paragraph ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}>
                  {memory.content}
                </Paragraph>
                <small style={{ color: '#999' }}>
                  {new Date(memory.created_at).toLocaleString()}
                </small>
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  );
};

export default SearchMemory;