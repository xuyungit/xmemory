import React, { useState, useEffect, useRef } from 'react';
import { Form, Input, Button, message, DatePicker, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import { createMemory } from '../services/memoryService';
import { getUserID } from '../utils/userStorage';
import dayjs from 'dayjs';

const { TextArea } = Input;
const { Title } = Typography;

const CreateMemory: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const contentInputRef = useRef<any>(null);
  const navigate = useNavigate();
  
  useEffect(() => {
    // 组件挂载后，将焦点设置到记忆内容输入框
    if (contentInputRef.current) {
      setTimeout(() => {
        contentInputRef.current.focus();
      }, 100);
    }
  }, []);
  
  const onFinish = async (values: any) => {
    try {
      setLoading(true);
      const user_id = getUserID();
      
      if (!user_id) {
        message.error('用户未登录');
        return;
      }
      
      // 添加用户ID到表单数据
      values.user_id = user_id;
      
      // Format the date if it exists
      if (values.created_at) {
        values.created_at = dayjs(values.created_at).format('YYYY-MM-DD HH:mm:ss');
      }
      
      await createMemory(values);
      message.success('记忆创建成功！');
      form.resetFields(['content', 'created_at']);
    } catch (error) {
      message.error('创建记忆失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      maxWidth: 600, 
      margin: '0 auto',
      padding: '0 16px',
      width: '100%'
    }}>
      <Title 
        level={3} 
        style={{ 
          textAlign: 'center', 
          marginBottom: 24,
          fontSize: 'calc(1.1rem + 0.5vw)'
        }}
      >
        记录新记忆
      </Title>
      
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Form.Item
          name="content"
          label="记忆内容"
          rules={[{ required: true, message: '请输入记忆内容' }]}
        >
          <TextArea 
            rows={4} 
            placeholder="请输入记忆内容" 
            style={{ resize: 'vertical' }}
            ref={contentInputRef}
          />
        </Form.Item>

        <Form.Item
          name="created_at"
          label="创建时间"
        >
          <DatePicker
            showTime
            format="YYYY-MM-DD HH:mm:ss"
            placeholder="选择或输入创建时间（可选）"
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            保存记忆
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default CreateMemory;