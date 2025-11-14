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
  Descriptions,
} from 'antd'
import { PlusOutlined, SyncOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import { datasourceAPI } from '@/services/api'

const { TextArea } = Input

export default function DataSource() {
  const [datasources, setDatasources] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedDatasource, setSelectedDatasource] = useState<any>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadDatasources()
  }, [])

  const loadDatasources = async () => {
    setLoading(true)
    try {
      const data = await datasourceAPI.list()
      setDatasources(data)
    } catch (error) {
      message.error('加载数据源失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (values: any) => {
    try {
      // 解析JSON字段
      const data = {
        ...values,
        config: typeof values.config === 'string' ? JSON.parse(values.config) : values.config,
        schema_info: values.schema_info ? (typeof values.schema_info === 'string' ? JSON.parse(values.schema_info) : values.schema_info) : null,
        examples: values.examples ? (typeof values.examples === 'string' ? JSON.parse(values.examples) : values.examples) : null,
      }
      await datasourceAPI.create(data)
      message.success('创建成功')
      setModalVisible(false)
      form.resetFields()
      loadDatasources()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建失败')
    }
  }

  const handleSync = async (id: string) => {
    try {
      await datasourceAPI.sync(id)
      message.success('同步成功')
      loadDatasources()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '同步失败')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await datasourceAPI.delete(id)
      message.success('删除成功')
      loadDatasources()
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
      title: '状态',
      dataIndex: 'sync_status',
      key: 'sync_status',
      render: (status: string) => (
        <Tag color={status === 'success' ? 'green' : status === 'failed' ? 'red' : 'default'}>
          {status}
        </Tag>
      ),
    },
    {
      title: '文档数',
      dataIndex: 'total_documents',
      key: 'total_documents',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedDatasource(record)
              setDetailModalVisible(true)
            }}
            size="small"
          >
            详情
          </Button>
          <Button
            icon={<SyncOutlined />}
            onClick={() => handleSync(record.id)}
            size="small"
          >
            同步
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
        <h1>数据源管理</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
        >
          添加数据源
        </Button>
      </div>

      <Table
        dataSource={datasources}
        columns={columns}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title="添加数据源"
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
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
            <TextArea rows={3} />
          </Form.Item>

          <Form.Item
            name="type"
            label="类型"
            rules={[{ required: true, message: '请选择类型' }]}
          >
            <Select>
              <Select.Option value="local_file">本地文件</Select.Option>
              <Select.Option value="database">数据库</Select.Option>
              <Select.Option value="api">API</Select.Option>
              <Select.Option value="web_crawler">网页爬虫</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="config"
            label="配置（JSON格式）"
            rules={[{ required: true, message: '请输入配置' }]}
          >
            <TextArea rows={6} placeholder='{"file_path": "/path/to/files"}' />
          </Form.Item>

          <Form.Item
            name="usage_doc"
            label="使用规范文档"
            tooltip="描述如何使用此数据源，如数据库表设计、API接口文档等"
          >
            <TextArea 
              rows={4} 
              placeholder="例如：本数据库包含用户信息和订单数据。查询时请注意：&#10;1. users表存储用户基本信息&#10;2. orders表存储订单信息&#10;3. 使用JOIN时注意性能"
            />
          </Form.Item>

          <Form.Item
            name="schema_info"
            label="结构信息（JSON格式）"
            tooltip="数据库schema、API参数等结构信息"
          >
            <TextArea 
              rows={6} 
              placeholder='{"tables": [{"name": "users", "columns": [{"name": "id", "type": "uuid"}]}]}'
            />
          </Form.Item>

          <Form.Item
            name="examples"
            label="使用示例（JSON数组）"
            tooltip="提供一些使用示例，帮助AI更好地理解如何使用"
          >
            <TextArea 
              rows={4} 
              placeholder='[{"description": "查询用户总数", "query": "SELECT COUNT(*) FROM users"}]'
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情模态框 */}
      <Modal
        title="数据源详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedDatasource && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="名称">{selectedDatasource.name}</Descriptions.Item>
            <Descriptions.Item label="描述">{selectedDatasource.description}</Descriptions.Item>
            <Descriptions.Item label="类型">
              <Tag>{selectedDatasource.type}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="配置">
              <pre style={{ maxHeight: 200, overflow: 'auto', background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                {JSON.stringify(selectedDatasource.config, null, 2)}
              </pre>
            </Descriptions.Item>
            {selectedDatasource.usage_doc && (
              <Descriptions.Item label="使用规范文档">
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{selectedDatasource.usage_doc}</pre>
              </Descriptions.Item>
            )}
            {selectedDatasource.schema_info && (
              <Descriptions.Item label="结构信息">
                <pre style={{ maxHeight: 200, overflow: 'auto', background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                  {JSON.stringify(selectedDatasource.schema_info, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
            {selectedDatasource.examples && (
              <Descriptions.Item label="使用示例">
                <pre style={{ maxHeight: 200, overflow: 'auto', background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                  {JSON.stringify(selectedDatasource.examples, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
            <Descriptions.Item label="状态">
              <Tag color={selectedDatasource.sync_status === 'success' ? 'green' : selectedDatasource.sync_status === 'failed' ? 'red' : 'default'}>
                {selectedDatasource.sync_status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="文档数">{selectedDatasource.total_documents}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

