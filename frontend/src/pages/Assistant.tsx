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
  Descriptions,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import api from '@/services/api'

const { TextArea } = Input

interface Assistant {
  id: string
  name: string
  description?: string
  llm_config_id?: string
  system_prompt?: string
  knowledge_base_ids: string[]
  datasource_ids: string[]
  interface_ids: string[]
  enable_knowledge_base: boolean
  enable_datasource: boolean
  enable_interface: boolean
  auto_route: boolean
  max_history: number
  is_default: boolean
  is_active: boolean
}

interface SelectOption {
  id: string
  name: string
}

export default function Assistant() {
  const [assistants, setAssistants] = useState<Assistant[]>([])
  const [llmConfigs, setLLMConfigs] = useState<SelectOption[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<SelectOption[]>([])
  const [datasources, setDatasources] = useState<SelectOption[]>([])
  const [interfaces, setInterfaces] = useState<SelectOption[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedAssistant, setSelectedAssistant] = useState<Assistant | null>(null)
  const [editingAssistant, setEditingAssistant] = useState<Assistant | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadAssistants()
    loadLLMConfigs()
    loadKnowledgeBases()
    loadDatasources()
    loadInterfaces()
  }, [])

  const loadAssistants = async () => {
    setLoading(true)
    try {
      const data = await api.get('/assistants')
      setAssistants(data)
    } catch (error) {
      message.error('加载助手列表失败')
    } finally {
      setLoading(false)
    }
  }

  const loadLLMConfigs = async () => {
    try {
      const data = await api.get('/llm-configs')
      setLLMConfigs(data.map((c: any) => ({ id: c.id, name: c.name })))
    } catch (error) {
      console.error('加载LLM配置失败:', error)
    }
  }

  const loadKnowledgeBases = async () => {
    try {
      const data = await api.get('/knowledge')
      setKnowledgeBases(data.map((kb: any) => ({ id: kb.id, name: kb.name })))
    } catch (error) {
      console.error('加载知识库列表失败:', error)
    }
  }

  const loadDatasources = async () => {
    try {
      const data = await api.get('/datasources')
      setDatasources(data.map((ds: any) => ({ id: ds.id, name: ds.name })))
    } catch (error) {
      console.error('加载数据源列表失败:', error)
    }
  }

  const loadInterfaces = async () => {
    try {
      const data = await api.get('/interfaces')
      setInterfaces(data.map((i: any) => ({ id: i.id, name: i.name })))
    } catch (error) {
      console.error('加载接口列表失败:', error)
    }
  }

  const handleCreate = async (values: any) => {
    try {
      if (editingAssistant) {
        await api.put(`/assistants/${editingAssistant.id}`, values)
        message.success('更新成功')
      } else {
        await api.post('/assistants', values)
        message.success('创建成功')
      }
      setModalVisible(false)
      form.resetFields()
      setEditingAssistant(null)
      loadAssistants()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const handleEdit = (record: Assistant) => {
    setEditingAssistant(record)
    form.setFieldsValue({
      name: record.name,
      description: record.description,
      llm_config_id: record.llm_config_id,
      system_prompt: record.system_prompt,
      knowledge_base_ids: record.knowledge_base_ids,
      datasource_ids: record.datasource_ids,
      interface_ids: record.interface_ids,
      enable_knowledge_base: record.enable_knowledge_base,
      enable_datasource: record.enable_datasource,
      enable_interface: record.enable_interface,
      auto_route: record.auto_route,
      max_history: record.max_history,
      is_default: record.is_default,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/assistants/${id}`)
      message.success('删除成功')
      loadAssistants()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Assistant) => (
        <>
          {text}
          {record.is_default && (
            <Tag color="blue" style={{ marginLeft: 8 }}>默认</Tag>
          )}
        </>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '智能路由',
      dataIndex: 'auto_route',
      key: 'auto_route',
      render: (autoRoute: boolean) => (
        <Tag color={autoRoute ? 'success' : 'default'}>
          {autoRoute ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '功能模块',
      key: 'modules',
      render: (_: any, record: Assistant) => (
        <Space>
          {record.enable_knowledge_base && (
            <Tag color="purple">知识库 ({record.knowledge_base_ids.length})</Tag>
          )}
          {record.enable_datasource && (
            <Tag color="green">数据源 ({record.datasource_ids.length})</Tag>
          )}
          {record.enable_interface && (
            <Tag color="orange">接口 ({record.interface_ids.length})</Tag>
          )}
        </Space>
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
      render: (_: any, record: Assistant) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedAssistant(record)
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
          <h1>AI助手配置</h1>
          <p style={{ color: '#666' }}>为不同场景创建专门的AI助手</p>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingAssistant(null)
            form.resetFields()
            setModalVisible(true)
          }}
        >
          创建助手
        </Button>
      </div>

      <Table
        dataSource={assistants}
        columns={columns}
        rowKey="id"
        loading={loading}
      />

      {/* 添加/编辑模态框 */}
      <Modal
        title={editingAssistant ? '编辑助手' : '创建助手'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
          setEditingAssistant(null)
        }}
        width={800}
      >
        <Form
          form={form}
          onFinish={handleCreate}
          layout="vertical"
          initialValues={{
            enable_knowledge_base: true,
            enable_datasource: true,
            enable_interface: true,
            auto_route: true,
            max_history: 10,
            is_default: false,
          }}
        >
          <Form.Item
            name="name"
            label="助手名称"
            rules={[{ required: true, message: '请输入助手名称' }]}
          >
            <Input placeholder="例如: 客服助手" />
          </Form.Item>

          <Form.Item name="description" label="助手描述">
            <TextArea rows={2} placeholder="简要描述助手的用途" />
          </Form.Item>

          <Form.Item name="llm_config_id" label="LLM配置">
            <Select placeholder="请选择LLM配置" allowClear>
              {llmConfigs.map((config) => (
                <Select.Option key={config.id} value={config.id}>
                  {config.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="system_prompt" label="系统提示词">
            <TextArea rows={4} placeholder="例如: 你是一个专业的客服代表..." />
          </Form.Item>

          <Form.Item label="功能配置">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Form.Item name="enable_knowledge_base" valuePropName="checked" noStyle>
                <Checkbox>启用知识库检索</Checkbox>
              </Form.Item>
              <Form.Item
                noStyle
                shouldUpdate={(prev, curr) => prev.enable_knowledge_base !== curr.enable_knowledge_base}
              >
                {({ getFieldValue }) =>
                  getFieldValue('enable_knowledge_base') ? (
                    <Form.Item name="knowledge_base_ids" style={{ marginLeft: 24 }}>
                      <Select
                        mode="multiple"
                        placeholder="选择知识库"
                        style={{ width: '100%' }}
                      >
                        {knowledgeBases.map((kb) => (
                          <Select.Option key={kb.id} value={kb.id}>
                            {kb.name}
                          </Select.Option>
                        ))}
                      </Select>
                    </Form.Item>
                  ) : null
                }
              </Form.Item>

              <Form.Item name="enable_datasource" valuePropName="checked" noStyle>
                <Checkbox>启用数据源查询</Checkbox>
              </Form.Item>
              <Form.Item
                noStyle
                shouldUpdate={(prev, curr) => prev.enable_datasource !== curr.enable_datasource}
              >
                {({ getFieldValue }) =>
                  getFieldValue('enable_datasource') ? (
                    <Form.Item name="datasource_ids" style={{ marginLeft: 24 }}>
                      <Select
                        mode="multiple"
                        placeholder="选择数据源"
                        style={{ width: '100%' }}
                      >
                        {datasources.map((ds) => (
                          <Select.Option key={ds.id} value={ds.id}>
                            {ds.name}
                          </Select.Option>
                        ))}
                      </Select>
                    </Form.Item>
                  ) : null
                }
              </Form.Item>

              <Form.Item name="enable_interface" valuePropName="checked" noStyle>
                <Checkbox>启用接口调用</Checkbox>
              </Form.Item>
              <Form.Item
                noStyle
                shouldUpdate={(prev, curr) => prev.enable_interface !== curr.enable_interface}
              >
                {({ getFieldValue }) =>
                  getFieldValue('enable_interface') ? (
                    <Form.Item name="interface_ids" style={{ marginLeft: 24 }}>
                      <Select
                        mode="multiple"
                        placeholder="选择接口"
                        style={{ width: '100%' }}
                      >
                        {interfaces.map((intf) => (
                          <Select.Option key={intf.id} value={intf.id}>
                            {intf.name}
                          </Select.Option>
                        ))}
                      </Select>
                    </Form.Item>
                  ) : null
                }
              </Form.Item>
            </Space>
          </Form.Item>

          <Form.Item name="auto_route" valuePropName="checked">
            <Checkbox>启用智能路由（自动判断使用哪种服务）</Checkbox>
          </Form.Item>

          <Form.Item name="max_history" label="最大历史消息数">
            <InputNumber min={1} max={50} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="is_default" valuePropName="checked">
            <Checkbox>设为默认助手</Checkbox>
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情模态框 */}
      <Modal
        title="助手详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={700}
      >
        {selectedAssistant && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="名称">{selectedAssistant.name}</Descriptions.Item>
            <Descriptions.Item label="描述">{selectedAssistant.description}</Descriptions.Item>
            <Descriptions.Item label="系统提示词">
              <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                {selectedAssistant.system_prompt || '未设置'}
              </pre>
            </Descriptions.Item>
            <Descriptions.Item label="智能路由">
              <Tag color={selectedAssistant.auto_route ? 'success' : 'default'}>
                {selectedAssistant.auto_route ? '启用' : '禁用'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="功能模块">
              <Space>
                {selectedAssistant.enable_knowledge_base && (
                  <Tag color="purple">
                    知识库 ({selectedAssistant.knowledge_base_ids.length})
                  </Tag>
                )}
                {selectedAssistant.enable_datasource && (
                  <Tag color="green">
                    数据源 ({selectedAssistant.datasource_ids.length})
                  </Tag>
                )}
                {selectedAssistant.enable_interface && (
                  <Tag color="orange">
                    接口 ({selectedAssistant.interface_ids.length})
                  </Tag>
                )}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="历史消息数">
              {selectedAssistant.max_history}
            </Descriptions.Item>
            <Descriptions.Item label="默认助手">
              {selectedAssistant.is_default ? '是' : '否'}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={selectedAssistant.is_active ? 'success' : 'default'}>
                {selectedAssistant.is_active ? '启用' : '禁用'}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}
