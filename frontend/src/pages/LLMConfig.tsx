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
  InputNumber,
  Checkbox,
  Card,
  Descriptions,
  AutoComplete,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import api from '@/services/api'

const { TextArea } = Input

interface LLMProvider {
  value: string
  label: string
  models: string[]
  default_base: string
}

interface LLMConfig {
  id: string
  name: string
  provider: string
  model_name: string
  api_base?: string
  temperature: number
  max_tokens: number
  is_default: boolean
  is_active: boolean
  has_api_key: boolean
}

export default function LLMConfig() {
  const [configs, setConfigs] = useState<LLMConfig[]>([])
  const [providers, setProviders] = useState<LLMProvider[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedConfig, setSelectedConfig] = useState<LLMConfig | null>(null)
  const [editingConfig, setEditingConfig] = useState<LLMConfig | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadProviders()
    loadConfigs()
  }, [])

  const loadProviders = async () => {
    try {
      const response = await api.get('/llm-configs/providers/list')
      setProviders(response.providers)
    } catch (error) {
      message.error('加载提供商列表失败')
      console.error('加载提供商失败:', error)
    }
  }

  const loadConfigs = async () => {
    setLoading(true)
    try {
      const data = await api.get('/llm-configs')
      setConfigs(data)
    } catch (error) {
      message.error('加载配置列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (values: any) => {
    try {
      if (editingConfig) {
        await api.put(`/llm-configs/${editingConfig.id}`, values)
        message.success('更新成功')
      } else {
        await api.post('/llm-configs', values)
        message.success('创建成功')
      }
      setModalVisible(false)
      form.resetFields()
      setEditingConfig(null)
      loadConfigs()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const handleEdit = (record: LLMConfig) => {
    setEditingConfig(record)
    form.setFieldsValue({
      name: record.name,
      provider: record.provider,
      model_name: record.model_name,
      api_base: record.api_base,
      temperature: record.temperature,
      max_tokens: record.max_tokens,
      is_default: record.is_default,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/llm-configs/${id}`)
      message.success('删除成功')
      loadConfigs()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleProviderChange = (provider: string) => {
    const selectedProvider = providers.find(p => p.value === provider)
    if (selectedProvider) {
      form.setFieldsValue({
        api_base: selectedProvider.default_base,
        model_name: selectedProvider.models[0] || '',
      })
    }
  }

  const getProviderLabel = (value: string) => {
    return providers.find(p => p.value === value)?.label || value
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: LLMConfig) => (
        <>
          {text}
          {record.is_default && (
            <Tag color="blue" style={{ marginLeft: 8 }}>默认</Tag>
          )}
        </>
      ),
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider: string) => getProviderLabel(provider),
    },
    {
      title: '模型',
      dataIndex: 'model_name',
      key: 'model_name',
    },
    {
      title: 'Temperature',
      dataIndex: 'temperature',
      key: 'temperature',
    },
    {
      title: 'Max Tokens',
      dataIndex: 'max_tokens',
      key: 'max_tokens',
    },
    {
      title: 'API密钥',
      dataIndex: 'has_api_key',
      key: 'has_api_key',
      render: (hasKey: boolean) => (
        <Tag color={hasKey ? 'success' : 'default'}>
          {hasKey ? '已配置' : '未配置'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: LLMConfig) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedConfig(record)
              setDetailModalVisible(true)
            }}
            size="small"
          >
            详情
          </Button>
          <Button
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            编辑
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
        <div>
          <h1>LLM模型配置</h1>
          <p style={{ color: '#666' }}>配置和管理您的大语言模型</p>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingConfig(null)
            form.resetFields()
            setModalVisible(true)
          }}
        >
          添加配置
        </Button>
      </div>

      <Table
        dataSource={configs}
        columns={columns}
        rowKey="id"
        loading={loading}
      />

      {/* 添加/编辑模态框 */}
      <Modal
        title={editingConfig ? '编辑配置' : '添加配置'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
          setEditingConfig(null)
        }}
        width={600}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item
            name="name"
            label="配置名称"
            rules={[{ required: true, message: '请输入配置名称' }]}
          >
            <Input placeholder="例如: 我的GPT-4配置" />
          </Form.Item>

          <Form.Item
            name="provider"
            label="提供商"
            rules={[{ required: true, message: '请选择提供商' }]}
          >
            <Select
              placeholder="请选择提供商"
              onChange={handleProviderChange}
              showSearch
              optionFilterProp="children"
            >
              {providers.map((provider) => (
                <Select.Option key={provider.value} value={provider.value}>
                  {provider.label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => prevValues.provider !== currentValues.provider}
          >
            {({ getFieldValue }) => {
              const currentProvider = getFieldValue('provider')
              const provider = providers.find(p => p.value === currentProvider)
              return provider ? (
                <>
                  <Form.Item
                    name="model_name"
                    label="模型名称"
                    rules={[{ required: true, message: '请输入或选择模型' }]}
                    extra="可以从列表选择或手动输入模型名称"
                  >
                    <AutoComplete
                      placeholder="请选择或输入模型名称（如：gpt-4, gpt-4-turbo）"
                      options={provider.models.map((model) => ({
                        value: model,
                        label: model,
                      }))}
                      filterOption={(inputValue, option) =>
                        option!.value.toUpperCase().indexOf(inputValue.toUpperCase()) !== -1
                      }
                    />
                  </Form.Item>

                  <Form.Item
                    name="api_key"
                    label={editingConfig ? 'API密钥（留空则不修改）' : 'API密钥'}
                    rules={editingConfig ? [] : [{ required: true, message: '请输入API密钥' }]}
                  >
                    <Input.Password placeholder="sk-..." />
                  </Form.Item>

                  <Form.Item name="api_base" label="API Base URL">
                    <Input placeholder="https://api.openai.com/v1" />
                  </Form.Item>

                  <Form.Item name="temperature" label="Temperature" initialValue={0.7}>
                    <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>

                  <Form.Item name="max_tokens" label="Max Tokens" initialValue={2000}>
                    <InputNumber min={1} max={128000} style={{ width: '100%' }} />
                  </Form.Item>

                  <Form.Item name="is_default" valuePropName="checked">
                    <Checkbox>设为默认配置</Checkbox>
                  </Form.Item>
                </>
              ) : null
            }}
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情模态框 */}
      <Modal
        title="配置详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={600}
      >
        {selectedConfig && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="名称">{selectedConfig.name}</Descriptions.Item>
            <Descriptions.Item label="提供商">
              {getProviderLabel(selectedConfig.provider)}
            </Descriptions.Item>
            <Descriptions.Item label="模型">{selectedConfig.model_name}</Descriptions.Item>
            <Descriptions.Item label="API Base URL">
              {selectedConfig.api_base || '默认'}
            </Descriptions.Item>
            <Descriptions.Item label="Temperature">{selectedConfig.temperature}</Descriptions.Item>
            <Descriptions.Item label="Max Tokens">{selectedConfig.max_tokens}</Descriptions.Item>
            <Descriptions.Item label="API密钥">
              <Tag color={selectedConfig.has_api_key ? 'success' : 'default'}>
                {selectedConfig.has_api_key ? '已配置' : '未配置'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="默认配置">
              {selectedConfig.is_default ? '是' : '否'}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={selectedConfig.is_active ? 'success' : 'default'}>
                {selectedConfig.is_active ? '启用' : '禁用'}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}
