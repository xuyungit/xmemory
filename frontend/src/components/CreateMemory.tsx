import React, { useState, useEffect } from 'react';
import { Form, Input, Button, message, DatePicker } from 'antd';
import { createMemory } from '../services/memoryService';
import { getUserID, setUserID } from '../utils/userStorage';
import dayjs from 'dayjs';

const { TextArea } = Input;

const CreateMemory: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const savedUserID = getUserID();
    if (savedUserID) {
      form.setFieldsValue({ user_id: savedUserID });
    }
  }, [form]);

  const onFinish = async (values: any) => {
    try {
      setLoading(true);
      setUserID(values.user_id);
      
      // Format the date if it exists
      if (values.created_at) {
        values.created_at = dayjs(values.created_at).format('YYYY-MM-DD HH:mm:ss');
      }
      
      await createMemory(values);
      message.success('记忆创建成功！');
      form.resetFields(['title', 'content', 'created_at']);
      // Keep the user_id field value
      form.setFieldsValue({ user_id: values.user_id });
    } catch (error) {
      message.error('创建记忆失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Form.Item
          name="user_id"
          label="用户ID"
          rules={[{ required: true, message: '请输入用户ID' }]}
        >
          <Input placeholder="请输入用户ID" />
        </Form.Item>

        <Form.Item
          name="title"
          label="记忆标题"
        >
          <Input placeholder="请输入记忆标题（可选）" />
        </Form.Item>

        <Form.Item
          name="content"
          label="记忆内容"
          rules={[{ required: true, message: '请输入记忆内容' }]}
        >
          <TextArea rows={4} placeholder="请输入记忆内容" />
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