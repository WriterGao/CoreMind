import { useEffect, useState } from 'react'
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  message,
  Space,
  Tag,
  Popconfirm,
} from 'antd'
import { PlusOutlined, PlayCircleOutlined, DeleteOutlined } from '@ant-design/icons'
import { interfaceAPI } from '@/services/api'

const { TextArea } = Input

export default function Interface() {
  const [interfaces, setInterfaces] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadInterfaces()
  }, [])

  const loadInterfaces = async () => {
    setLoading(true)
    try {
      const data = await interfaceAPI.list()
      setInterfaces(data)
    } catch (error) {
      message.error('加载接口失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (values: any) => {
    try {
      // 解析JSON字符串
      if (values.config) {
        values.config = JSON.parse(values.config)
      }
      if (values.parameters) {
        values.parameters = JSON.parse(values.parameters)
      }
      
      await interfaceAPI.create(values)
      message.success('创建成功')
      setModalVisible(false)
      form.resetFields()
      loadInterfaces()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建失败')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await interfaceAPI.delete(id)
      message.success('删除成功')
      loadInterfaces()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: '执行次数',
      dataIndex: 'execution_count',
      key: 'execution_count',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button
            icon={<PlayCircleOutlined />}
            size="small"
          >
            执行
          </Button>
          <Popconfirm
            title="确定删除吗？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button icon={<DeleteOutlined />} danger size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h1>接口管理</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
        >
          添加接口
        </Button>
      </div>

      <Table
        dataSource={interfaces}
        columns={columns}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title="添加接口"
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        width={720}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>

          <Form.Item
            name="type"
            label="类型"
            rules={[{ required: true, message: '请选择类型' }]}
          >
            <Select>
              <Select.Option value="function">函数</Select.Option>
              <Select.Option value="api">API</Select.Option>
              <Select.Option value="database">数据库</Select.Option>
              <Select.Option value="file">文件</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="config"
            label="配置（JSON格式）"
            rules={[{ required: true, message: '请输入配置' }]}
          >
            <TextArea 
              rows={4} 
              placeholder='{"url": "https://api.example.com", "method": "GET"}'
            />
          </Form.Item>

          <Form.Item
            name="parameters"
            label="参数定义（JSON Schema）"
          >
            <TextArea 
              rows={4} 
              placeholder='{"type": "object", "properties": {...}}'
            />
          </Form.Item>

          <Form.Item
            name="code"
            label="函数代码（仅函数类型）"
          >
            <TextArea 
              rows={6}
              placeholder="def main(param1, param2):\n    return result"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

