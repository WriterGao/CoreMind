import { useEffect, useState, useRef } from 'react'
import {
  Layout,
  List,
  Card,
  Input,
  Button,
  Modal,
  Form,
  Select,
  message,
  Space,
  Avatar,
  Popconfirm,
  Tag,
} from 'antd'
import {
  SendOutlined,
  PlusOutlined,
  RobotOutlined,
  UserOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { chatV2API, assistantAPI } from '@/services/api'

const { Sider, Content } = Layout
const { TextArea } = Input

export default function Chat() {
  const [conversations, setConversations] = useState<any[]>([])
  const [currentConversation, setCurrentConversation] = useState<any>(null)
  const [messages, setMessages] = useState<any[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [assistants, setAssistants] = useState<any[]>([])
  const [form] = Form.useForm()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<any>(null)

  useEffect(() => {
    loadConversations()
    loadAssistants()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadConversations = async () => {
    try {
      const data = await chatV2API.listConversations()
      setConversations(data)
      if (data.length > 0 && !currentConversation) {
        selectConversation(data[0].id)
      }
    } catch (error) {
      message.error('加载对话列表失败')
    }
  }

  const loadAssistants = async () => {
    try {
      const data = await assistantAPI.list()
      setAssistants(data)
    } catch (error) {
      console.error('加载助手列表失败', error)
    }
  }

  const selectConversation = async (id: string) => {
    try {
      const conv = await chatV2API.getConversation(id)
      setCurrentConversation(conv)
      
      const msgs = await chatV2API.getMessages(id)
      setMessages(msgs)
    } catch (error) {
      message.error('加载对话失败')
    }
  }

  const handleCreateConversation = async (values: any) => {
    try {
      const conv = await chatV2API.createConversation(values)
      message.success('创建成功')
      setModalVisible(false)
      form.resetFields()
      await loadConversations()
      selectConversation(conv.id)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建失败')
    }
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !currentConversation) {
      return
    }

    const userMessage = inputMessage
    setInputMessage('')
    setLoading(true)

    // 添加用户消息到界面
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
    }])

    try {
      const response = await chatV2API.sendMessage(currentConversation.id, {
        message: userMessage,
        stream: false,
      })

      // 添加AI回复到界面
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.content,
      }])
    } catch (error: any) {
      message.error(error.response?.data?.detail || '发送失败')
      // 移除用户消息
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
      // 重新聚焦输入框
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
    }
  }

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await chatV2API.deleteConversation(id)
      message.success('删除成功')
      await loadConversations()
      if (currentConversation?.id === id) {
        setCurrentConversation(null)
        setMessages([])
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  return (
    <Layout style={{ height: 'calc(100vh - 112px)' }}>
      <Sider width={250} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
            block
          >
            新建对话
          </Button>
        </div>
        
        <List
          dataSource={conversations}
          renderItem={(item: any) => (
            <List.Item
              style={{
                padding: '12px 16px',
                cursor: 'pointer',
                background: currentConversation?.id === item.id ? '#e6f7ff' : 'transparent',
              }}
              onClick={() => selectConversation(item.id)}
              actions={[
                <Popconfirm
                  title="确定要删除这个对话吗？"
                  onConfirm={(e) => handleDeleteConversation(item.id, e as any)}
                  onCancel={(e) => e?.stopPropagation()}
                  onClick={(e) => e.stopPropagation()}
                >
                  <Button
                    type="text"
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={(e) => e.stopPropagation()}
                  />
                </Popconfirm>
              ]}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <span>{item.title}</span>
                    {item.assistant_name && (
                      <Tag color="blue" size="small">{item.assistant_name}</Tag>
                    )}
                  </Space>
                }
                description={`${item.message_count} 条消息`}
              />
            </List.Item>
          )}
        />
      </Sider>

      <Content style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
          {messages.map((msg, index) => (
            <div
              key={index}
              style={{
                marginBottom: 16,
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              {msg.role === 'assistant' && (
                <Avatar icon={<RobotOutlined />} style={{ marginRight: 8 }} />
              )}
              
              <Card
                style={{
                  maxWidth: '70%',
                  background: msg.role === 'user' ? '#1890ff' : '#f5f5f5',
                  color: msg.role === 'user' ? 'white' : 'inherit',
                }}
                bodyStyle={{ padding: 12 }}
              >
                {msg.role === 'assistant' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  <div>{msg.content}</div>
                )}
              </Card>

              {msg.role === 'user' && (
                <Avatar icon={<UserOutlined />} style={{ marginLeft: 8 }} />
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div style={{ padding: 16, borderTop: '1px solid #f0f0f0' }}>
          <Space.Compact style={{ width: '100%' }}>
            <TextArea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
              placeholder="输入消息... (Shift+Enter换行)"
              autoSize={{ minRows: 1, maxRows: 4 }}
              disabled={!currentConversation || loading}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              disabled={!currentConversation || loading}
              loading={loading}
            >
              发送
            </Button>
          </Space.Compact>
        </div>
      </Content>

      <Modal
        title="新建对话"
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
      >
        <Form form={form} onFinish={handleCreateConversation} layout="vertical">
          <Form.Item
            name="title"
            label="对话标题"
            initialValue="新对话"
          >
            <Input placeholder="请输入对话标题" />
          </Form.Item>

          <Form.Item 
            name="assistant_id" 
            label="选择助手" 
            rules={[{ required: true, message: '请选择助手' }]}
          >
            <Select placeholder="选择AI助手配置">
              {assistants.map((assistant: any) => (
                <Select.Option key={assistant.id} value={assistant.id}>
                  {assistant.name} {assistant.description && `- ${assistant.description}`}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="system_prompt" label="系统提示词（可选）">
            <TextArea 
              rows={3} 
              placeholder="留空则使用助手配置中的系统提示词"
            />
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  )
}

