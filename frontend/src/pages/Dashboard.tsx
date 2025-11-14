import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic } from 'antd'
import {
  DatabaseOutlined,
  BookOutlined,
  ApiOutlined,
  MessageOutlined,
} from '@ant-design/icons'
import { datasourceAPI, knowledgeAPI, interfaceAPI, chatAPI } from '@/services/api'

export default function Dashboard() {
  const [stats, setStats] = useState({
    datasources: 0,
    knowledgeBases: 0,
    interfaces: 0,
    conversations: 0,
  })

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const [datasources, knowledgeBases, interfaces, conversations] = await Promise.all([
        datasourceAPI.list(),
        knowledgeAPI.list(),
        interfaceAPI.list(),
        chatAPI.listConversations(),
      ])

      setStats({
        datasources: datasources.length,
        knowledgeBases: knowledgeBases.length,
        interfaces: interfaces.length,
        conversations: conversations.length,
      })
    } catch (error) {
      console.error('加载统计数据失败', error)
    }
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>仪表盘</h1>
      
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="数据源"
              value={stats.datasources}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="知识库"
              value={stats.knowledgeBases}
              prefix={<BookOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="接口"
              value={stats.interfaces}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="对话"
              value={stats.conversations}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: 24 }} title="欢迎使用 CoreMind">
        <h3>快速开始</h3>
        <ul>
          <li>1. 在"数据源"页面添加您的数据源（文件、数据库、API等）</li>
          <li>2. 在"知识库"页面创建知识库并上传文档</li>
          <li>3. 在"接口"页面配置自定义接口</li>
          <li>4. 在"对话"页面开始与AI助手对话</li>
        </ul>

        <h3>核心特性</h3>
        <ul>
          <li>🗂️ <strong>多数据源支持</strong>：本地文件、数据库、API、云存储、网页爬虫</li>
          <li>🧠 <strong>智能知识库</strong>：向量化存储、语义检索、知识图谱</li>
          <li>🔌 <strong>接口自定义</strong>：可视化配置、灵活扩展</li>
          <li>💬 <strong>对话管理</strong>：多轮对话、上下文记忆、个性化回复</li>
        </ul>
      </Card>
    </div>
  )
}

