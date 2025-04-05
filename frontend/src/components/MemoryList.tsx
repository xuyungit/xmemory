import React, { useState, useEffect, useCallback } from 'react';
import { Typography, Spin, Empty, Input, Form, Table, TablePaginationConfig } from 'antd';
import { getMemories, PaginatedResponse } from '../services/memoryService';
import { getUserID, setUserID } from '../utils/userStorage';

const { Title } = Typography;
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
  const [pagination, setPagination] = useState<TablePaginationConfig>({
    current: 1,
    pageSize: 10,
    total: 0,
    showSizeChanger: true,
    pageSizeOptions: ['10', '20', '50'],
    showTotal: (total, range) => `${range[0]}-${range[1]} 条，共 ${total} 条`
  });
  const [sortInfo, setSortInfo] = useState<{
    sortBy: string;
    sortOrder: string;
  }>({
    sortBy: 'created_at',
    sortOrder: 'desc'
  });
  const [form] = Form.useForm();

  // 表格列定义
  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180, // 设置时间列固定宽度
      render: (text: string) => new Date(text).toLocaleString(),
      sorter: true,
      defaultSortOrder: 'descend' as 'descend',
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: { showTitle: false },
      render: (text: string) => (
        <div style={{ 
          overflow: 'hidden', 
          textOverflow: 'ellipsis', 
          display: '-webkit-box', 
          WebkitLineClamp: 2, // 从3行减少到2行，减少行高
          WebkitBoxOrient: 'vertical' 
        }}>
          {text}
        </div>
      ),
    },
  ];

  const fetchMemories = useCallback(async () => {
    if (!user_id) return;
    
    try {
      setLoading(true);
      const { current = 1, pageSize = 10 } = pagination;
      const { sortBy, sortOrder } = sortInfo;
      
      const data: PaginatedResponse = await getMemories(
        user_id, 
        current as number, 
        pageSize as number,
        sortBy,
        sortOrder
      );
      
      setMemories(data.memories);
      setPagination(prev => ({
        ...prev,
        current: data.page,
        pageSize: data.page_size,
        total: data.total,
      }));
    } catch (error) {
      console.error('获取记忆列表失败:', error);
    } finally {
      setLoading(false);
    }
  }, [user_id, pagination.current, pagination.pageSize, sortInfo]);

  useEffect(() => {
    const savedUserID = getUserID();
    if (savedUserID) {
      setUser_id(savedUserID);
      form.setFieldsValue({ user_id: savedUserID });
    }
  }, [form]);

  useEffect(() => {
    if (user_id) {
      fetchMemories();
    }
  }, [user_id, fetchMemories]);

  const onSearch = (value: string) => {
    setUser_id(value);
    setUserID(value);
    // 重置分页到第一页
    setPagination(prev => ({
      ...prev,
      current: 1,
    }));
  };

  // 处理表格分页、排序、筛选变化
  const handleTableChange = (
    pagination: TablePaginationConfig,
    filters: any,
    sorter: any,
  ) => {
    setPagination(pagination);
    
    // 处理排序
    if (sorter && sorter.field) {
      const sortBy = sorter.field.toString();
      const sortOrder = sorter.order === 'ascend' ? 'asc' : 'desc';
      setSortInfo({ sortBy, sortOrder });
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Title level={2} style={{ textAlign: 'center', marginBottom: 24 }}>
        记忆列表
      </Title>

      <div style={{ marginBottom: 24 }}>
        <Form form={form}>
          <Form.Item name="user_id" noStyle>
            <Search
              placeholder="输入用户ID查看记忆"
              allowClear
              enterButton="搜索"
              size="large"
              onSearch={onSearch}
            />
          </Form.Item>
        </Form>
      </div>
      
      {loading && memories.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </div>
      ) : memories.length === 0 ? (
        <Empty description={user_id ? "该用户暂无记忆" : "请输入用户ID查看记忆"} />
      ) : (
        <Table 
          dataSource={memories} 
          columns={columns}
          rowKey="id"
          pagination={pagination}
          onChange={handleTableChange}
          bordered
          size="small"
          scroll={{ x: 'max-content' }}
          style={{ overflowX: 'auto' }}
          loading={loading}
        />
      )}
    </div>
  );
};

export default MemoryList;