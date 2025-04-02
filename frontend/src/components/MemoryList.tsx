import React, { useState, useEffect } from 'react';
import { List, Card, Typography, Spin, Empty, Input, Button } from 'antd';
import { getMemories } from '../services/memoryService';
import { getUserID, setUserID } from '../utils/userStorage';

const { Title, Paragraph } = Typography;
const { Search } = Input;

interface Memory {
  id: string;
  user_id: string;
  title?: string;
  content: string;
  created_at: string;
}

const MemoryList: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [user_id, setUser_id] = useState<string>('');

  useEffect(() => {
    const savedUserID = getUserID();
    if (savedUserID) {
      setUser_id(savedUserID);
    }
  }, []);

  useEffect(() => {
    if (user_id) {
      fetchMemories();
    }
  }, [user_id]);

  const fetchMemories = async () => {
    try {
      setLoading(true);
      const data = await getMemories(user_id);
      setMemories(data);
    } catch (error) {
      console.error('获取记忆列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSearch = (value: string) => {
    setUser_id(value);
    setUserID(value);
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Title level={2} style={{ textAlign: 'center', marginBottom: 24 }}>
        记忆列表
      </Title>

      <div style={{ marginBottom: 24 }}>
        <Search
          placeholder="输入用户ID查看记忆"
          allowClear
          enterButton="搜索"
          size="large"
          onSearch={onSearch}
        />
      </div>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </div>
      ) : memories.length === 0 ? (
        <Empty description={user_id ? "该用户暂无记忆" : "请输入用户ID查看记忆"} />
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

export default MemoryList; 