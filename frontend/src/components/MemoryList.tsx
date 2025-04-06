import React, { useState, useEffect, useCallback } from 'react';
import { Spin, Empty, Table, TablePaginationConfig, Button, Space, Tooltip, Row, Col, Select, Modal, message } from 'antd';
import { ReloadOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { Breakpoint } from 'antd/es/_util/responsiveObserver';
import { getMemories, deleteMemory, PaginatedResponse } from '../services/memoryService';
import { getUserID } from '../utils/userStorage';
import { getMemoryTypeOptions, MemoryTypeNames } from '../utils/memoryTypes';

interface Memory {
  id: string;
  user_id: string;
  title?: string;
  content: string;
  created_at: string;
  memory_type: string;
  tags: string[];
  _id?: string; // 添加_id字段，用于删除操作
}

const MemoryList: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [user_id, setUser_id] = useState<string>('');
  const [refreshing, setRefreshing] = useState(false);
  const [memoryType, setMemoryType] = useState<string | null>("all");
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [deleting, setDeleting] = useState(false);
  const navigate = useNavigate();
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

  // 表格列定义
  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text: string) => new Date(text).toLocaleString(),
      sorter: true,
      defaultSortOrder: 'descend' as 'descend',
      responsive: ['md' as Breakpoint], // 修复为 Breakpoint 类型
    },
    {
      title: '类型',
      dataIndex: 'memory_type',
      key: 'memory_type',
      width: 100, // 减小类型列宽度，从120px到100px
      render: (type: string) => MemoryTypeNames[type] || type,
      responsive: ['sm' as Breakpoint], // 修复为 Breakpoint 类型
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: { showTitle: false },
      width: 'auto', // 添加这一行，让内容列自适应剩余宽度
      render: (text: string, record: any) => (
        <Tooltip title={text.split('\n').map((line, i) => (
          <div key={i}>{line}</div>
        ))}>
          <div style={{ 
            overflow: 'hidden', 
            textOverflow: 'ellipsis', 
            display: '-webkit-box', 
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            whiteSpace: 'pre-line', // 保留换行符，同时允许自动换行
            wordBreak: 'break-word', // 确保长单词也能正确换行
            maxWidth: '100%', // 确保内容不会超出容器宽度
            width: '100%', // 占满可用空间
            wordWrap: 'break-word', // 兼容性更好的长文本换行
            minWidth: '0', // 添加这一行，允许元素缩小到小于其内容尺寸
          }}>
            {/* 在小屏幕上添加时间信息，因为时间列会被隐藏 */}
            {window.innerWidth < 768 && (
              <small style={{ display: 'block', color: '#999', marginBottom: 4 }}>
                {new Date(record.created_at).toLocaleString()}
              </small>
            )}
            {text}
          </div>
        </Tooltip>
      ),
    },
  ];

  const fetchMemories = useCallback(async (page?: number, pageSize?: number) => {
    if (!user_id) return;
    
    try {
      setLoading(true);
      // 使用传入的页码和每页数量，避免依赖pagination状态
      const current = page || 1;
      const size = pageSize || 10;
      const { sortBy, sortOrder } = sortInfo;
      
      // 处理记忆类型筛选，仅当不是"全部"时传递参数
      const typeFilter = memoryType && memoryType !== "all" ? memoryType : undefined;
      
      console.log(`获取第 ${current} 页数据，每页 ${size} 条`);
      const data: PaginatedResponse = await getMemories(
        user_id, 
        current, 
        size,
        sortBy,
        sortOrder,
        typeFilter
      );
      
      setMemories(data.memories);
      // 更新分页信息
      setPagination(prev => ({
        ...prev,
        current: current, // 确保页码与请求一致
        pageSize: data.page_size,
        total: data.total,
      }));
    } catch (error) {
      console.error('获取记忆列表失败:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user_id, sortInfo, memoryType]); // pagination不再是依赖项

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
  }, [user_id, fetchMemories]);

  // 监听分页状态变化，触发数据获取
  useEffect(() => {
    // 这里不需要做任何事情，避免死循环
    // 分页变化通过handleTableChange单独处理
  }, []);

  // 处理表格分页、排序、筛选变化
  const handleTableChange = (
    pagination: TablePaginationConfig,
    filters: any,
    sorter: any,
  ) => {
    // 先更新分页状态
    setPagination(pagination);
    
    // 处理排序
    if (sorter && sorter.field) {
      const sortBy = sorter.field.toString();
      const sortOrder = sorter.order === 'ascend' ? 'asc' : 'desc';
      setSortInfo({ sortBy, sortOrder });
    }
    
    // 加载对应页面的数据
    fetchMemories(pagination.current as number, pagination.pageSize as number);
  };

  // 处理手动刷新
  const handleRefresh = () => {
    setRefreshing(true);
    // 传递当前页码和每页条数，确保刷新当前页的数据
    fetchMemories(pagination.current as number, pagination.pageSize as number);
  };

  // 处理记忆类型过滤变化
  const handleTypeChange = (value: string) => {
    // 设置新的记忆类型
    setMemoryType(value);
    // 重置到第一页
    setPagination(prev => ({ ...prev, current: 1 }));
    
    // 不在这里调用fetchMemories，避免发送重复请求
    // memoryType状态更新后会触发useEffect中的fetchMemories
  };

  // 处理删除操作
  const handleDelete = async () => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除选中的记忆吗？',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        setDeleting(true);
        try {
          await Promise.all(selectedRowKeys.map(id => deleteMemory(id as string)));
          message.success('删除成功');
          setSelectedRowKeys([]);
          // 保留当前页码，传递当前分页参数
          fetchMemories(pagination.current as number, pagination.pageSize as number);
        } catch (error) {
          console.error('删除记忆失败:', error);
          message.error('删除失败');
        } finally {
          setDeleting(false);
        }
      },
    });
  };

  // 处理行选择变化
  const handleRowSelectionChange = (selectedRowKeys: React.Key[]) => {
    setSelectedRowKeys(selectedRowKeys);
  };

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '0 8px' }}>
      {/* 工具栏 */}
      <Row 
        justify="space-between" 
        style={{ marginBottom: 16 }}
        gutter={[8, 8]} // 添加栅格间距，改善小屏幕显示
        align="middle"
      >
        <Col xs={24} sm={12}>
          <Select
            placeholder="选择记忆类型"
            style={{ width: '100%', maxWidth: 150 }}
            options={getMemoryTypeOptions()}
            value={memoryType || "all"}
            onChange={handleTypeChange}
          />
        </Col>
        <Col xs={24} sm={12} style={{ textAlign: 'right' }}>
          <Space>
            <Tooltip title="刷新记忆列表">
              <Button 
                icon={<ReloadOutlined />} 
                onClick={handleRefresh}
                loading={refreshing}
              >
                刷新
              </Button>
            </Tooltip>
            <Tooltip title="删除选中的记忆">
              <Button 
                icon={<DeleteOutlined />} 
                onClick={handleDelete}
                disabled={selectedRowKeys.length === 0}
                loading={deleting}
                danger
              >
                删除
              </Button>
            </Tooltip>
          </Space>
        </Col>
      </Row>
      
      {loading && memories.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </div>
      ) : memories.length === 0 ? (
        <Empty description="暂无记忆" />
      ) : (
        <Table 
          dataSource={memories} 
          columns={columns}
          rowKey={(record) => record._id || record.id} // 优先使用 _id，如果不存在则使用 id
          pagination={{
            ...pagination,
            responsive: true, // 使分页组件自适应
            size: window.innerWidth < 576 ? 'small' : 'default', // 小屏幕使用小尺寸分页
          }}
          onChange={handleTableChange}
          bordered
          size="small"
          scroll={{ x: '100%' }} // 从 'max-content' 改为 '100%'，限制表格宽度
          style={{ overflowX: 'auto' }}
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: handleRowSelectionChange,
          }}
        />
      )}
    </div>
  );
};

export default MemoryList;