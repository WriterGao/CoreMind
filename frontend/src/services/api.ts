import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 认证API
export const authAPI = {
  register: (data: any) => api.post('/auth/register', data),
  login: (data: any) => api.post('/auth/login', new URLSearchParams(data), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }),
  me: () => api.get('/auth/me'),
}

// 数据源API
export const datasourceAPI = {
  list: () => api.get('/datasources'),
  create: (data: any) => api.post('/datasources', data),
  get: (id: string) => api.get(`/datasources/${id}`),
  delete: (id: string) => api.delete(`/datasources/${id}`),
  sync: (id: string) => api.post(`/datasources/${id}/sync`),
}

// 知识库API
export const knowledgeAPI = {
  list: () => api.get('/knowledge'),
  create: (data: any) => api.post('/knowledge', data),
  get: (id: string) => api.get(`/knowledge/${id}`),
  delete: (id: string) => api.delete(`/knowledge/${id}`),
  upload: (id: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/knowledge/${id}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  search: (id: string, query: string, topK: number = 5) => 
    api.post(`/knowledge/${id}/search`, { query, top_k: topK }),
}

// 接口API
export const interfaceAPI = {
  list: () => api.get('/interfaces'),
  create: (data: any) => api.post('/interfaces', data),
  get: (id: string) => api.get(`/interfaces/${id}`),
  delete: (id: string) => api.delete(`/interfaces/${id}`),
  execute: (id: string, parameters: any) => 
    api.post(`/interfaces/${id}/execute`, { parameters }),
}

// LLM配置API
export const llmConfigAPI = {
  list: () => api.get('/llm-configs'),
  create: (data: any) => api.post('/llm-configs', data),
  get: (id: string) => api.get(`/llm-configs/${id}`),
  update: (id: string, data: any) => api.put(`/llm-configs/${id}`, data),
  delete: (id: string) => api.delete(`/llm-configs/${id}`),
  getProviders: () => api.get('/llm-configs/providers/list'),
}

// 助手配置API
export const assistantAPI = {
  list: () => api.get('/assistants'),
  create: (data: any) => api.post('/assistants', data),
  get: (id: string) => api.get(`/assistants/${id}`),
  update: (id: string, data: any) => api.put(`/assistants/${id}`, data),
  delete: (id: string) => api.delete(`/assistants/${id}`),
}

// 对话API
export const chatAPI = {
  listConversations: () => api.get('/chat/conversations'),
  createConversation: (data: any) => api.post('/chat/conversations', data),
  getConversation: (id: string) => api.get(`/chat/conversations/${id}`),
  deleteConversation: (id: string) => api.delete(`/chat/conversations/${id}`),
  getMessages: (id: string) => api.get(`/chat/conversations/${id}/messages`),
  sendMessage: (id: string, data: any) => 
    api.post(`/chat/conversations/${id}/messages`, data),
}

// 对话API V2 (支持助手配置)
export const chatV2API = {
  listConversations: () => api.get('/chat-v2/conversations'),
  createConversation: (data: any) => api.post('/chat-v2/conversations', data),
  getConversation: (id: string) => api.get(`/chat-v2/conversations/${id}`),
  deleteConversation: (id: string) => api.delete(`/chat-v2/conversations/${id}`),
  getMessages: (id: string) => api.get(`/chat-v2/conversations/${id}/messages`),
  sendMessage: (id: string, data: any) => 
    api.post(`/chat-v2/conversations/${id}/messages`, data),
}

export default api

