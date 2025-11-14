import { useEffect, useState } from 'react'
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  message,
  Space,
  Upload,
  Popconfirm,
} from 'antd'
import { PlusOutlined, UploadOutlined, DeleteOutlined } from '@ant-design/icons'
import { knowledgeAPI } from '@/services/api'

const { TextArea } = Input

export default function Knowledge() {
  const [knowledgeBases, setKnowledgeBases] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [selectedKbId, setSelectedKbId] = useState('')
  const [form] = Form.useForm()

  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  const loadKnowledgeBases = async () => {
    setLoading(true)
    try {
      const data = await knowledgeAPI.list()
      setKnowledgeBases(data)
    } catch (error) {
      message.error('加载知识库失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (values: any) => {
    try {
      await knowledgeAPI.create(values)
      message.success('创建成功')
      setModalVisible(false)
      form.resetFields()
      loadKnowledgeBases()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建失败')
    }
  }

  const handleUpload = async (file: File) => {
    try {
      await knowledgeAPI.upload(selectedKbId, file)
      message.success('上传成功')
      setUploadModalVisible(false)
      loadKnowledgeBases()
      return false
    } catch (error: any) {
      message.error(error.response?.data?.detail || '上传失败')
      return false
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await knowledgeAPI.delete(id)
      message.success('删除成功')
      loadKnowledgeBases()
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
      title: '嵌入模型',
      dataIndex: 'embedding_model',
      key: 'embedding_model',
    },
    {
      title: '文档数',
      dataIndex: 'total_documents',
      key: 'total_documents',
    },
    {
      title: '切片数',
      dataIndex: 'total_chunks',
      key: 'total_chunks',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button
            icon={<UploadOutlined />}
            onClick={() => {
              setSelectedKbId(record.id)
              setUploadModalVisible(true)
            }}
            size="small"
          >
            上传文档
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
        <h1>知识库管理</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
        >
          创建知识库
        </Button>
      </div>

      <Table
        dataSource={knowledgeBases}
        columns={columns}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title="创建知识库"
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

          <Form.Item name="embedding_model" label="嵌入模型" initialValue="text-embedding-ada-002">
            <Input />
          </Form.Item>

          <Form.Item name="chunk_size" label="切片大小" initialValue={1000}>
            <Input type="number" />
          </Form.Item>

          <Form.Item name="chunk_overlap" label="切片重叠" initialValue={200}>
            <Input type="number" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="上传文档"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
      >
        <Upload.Dragger
          name="file"
          multiple={false}
          beforeUpload={handleUpload}
          accept=".pdf,.docx,.xlsx,.txt,.csv,.md"
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持 PDF, DOCX, XLSX, TXT, CSV, MD 格式
          </p>
        </Upload.Dragger>
      </Modal>
    </div>
  )
}

