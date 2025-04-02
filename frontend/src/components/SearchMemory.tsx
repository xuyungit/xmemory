import React, { useState, useEffect } from 'react';
import { Form, Input, Button, List, Card, Typography, Spin, Empty } from 'antd';
import { searchMemories } from '../services/memoryService';
import { getUserID, setUserID } from '../utils/userStorage';

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

  useEffect(() => {
    const savedUserID = getUserID();
    if (savedUserID) {
      form.setFieldsValue({ user_id: savedUserID });
    }
  }, [form]);

  const onFinish = async (values: { user_id: string; searchText: string }) => {
    try {
      setLoading(true);
      setUserID(values.user_id);
      const data = await searchMemories(values.user_id, values.searchText);
      setMemories(data);
    } catch (error) {
      console.error('搜索记忆失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Title level={2} style={{ textAlign: 'center', marginBottom: 24 }}>
        查找记忆
      </Title>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        style={{ marginBottom: 24 }}
      >
        <Form.Item
          name="user_id"
          label="用户ID"
          rules={[{ required: true, message: '请输入用户ID' }]}
        >
          <Input placeholder="请输入用户ID" />
        </Form.Item>

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
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </div>
      ) : memories.length === 0 ? (
        <Empty description="未找到相关记忆" />
      ) : (
        <List
          grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 3, xl: 3, xxl: 3 }}
          dataSource={memories}
          renderItem={(memory) => (
            <List.Item>
              <Card
                title={memory.title || '无标题'}
                extra={<small>{memory.user_id}</small>}
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