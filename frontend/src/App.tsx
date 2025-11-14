import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import MainLayout from './layouts/MainLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import DataSource from './pages/DataSource'
import Knowledge from './pages/Knowledge'
import Interface from './pages/Interface'
import LLMConfig from './pages/LLMConfig'
import Assistant from './pages/Assistant'
import Chat from './pages/Chat'
import { useAuthStore } from './store/authStore'

function App() {
  const { token } = useAuthStore()

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      <Route path="/" element={token ? <MainLayout /> : <Navigate to="/login" />}>
        <Route index element={<Dashboard />} />
        <Route path="datasources" element={<DataSource />} />
        <Route path="knowledge" element={<Knowledge />} />
        <Route path="interfaces" element={<Interface />} />
        <Route path="llm-configs" element={<LLMConfig />} />
        <Route path="assistants" element={<Assistant />} />
        <Route path="chat" element={<Chat />} />
      </Route>
    </Routes>
  )
}

export default App

