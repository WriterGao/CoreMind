# CoreMind API文档

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (JWT)

## 认证接口

### 1. 用户注册

**接口**: `POST /auth/register`

**请求体**:
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "full_name": "测试用户"
}
```

**响应**:
```json
{
  "id": "uuid",
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "测试用户",
  "is_active": true
}
```

### 2. 用户登录

**接口**: `POST /auth/login`

**请求体** (application/x-www-form-urlencoded):
```
username=testuser&password=password123
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. 获取当前用户信息

**接口**: `GET /auth/me`

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "id": "uuid",
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "测试用户",
  "is_active": true
}
```

## 数据源接口

### 1. 创建数据源

**接口**: `POST /datasources`

**请求体**:
```json
{
  "name": "我的文档库",
  "description": "本地文档数据源",
  "type": "local_file",
  "config": {
    "file_path": "/path/to/documents",
    "recursive": true,
    "supported_extensions": [".pdf", ".docx", ".txt"]
  },
  "sync_frequency": 60
}
```

### 2. 获取数据源列表

**接口**: `GET /datasources`

### 3. 同步数据源

**接口**: `POST /datasources/{datasource_id}/sync`

### 4. 删除数据源

**接口**: `DELETE /datasources/{datasource_id}`

## 知识库接口

### 1. 创建知识库

**接口**: `POST /knowledge`

**请求体**:
```json
{
  "name": "技术文档库",
  "description": "技术相关的文档知识库",
  "embedding_model": "text-embedding-ada-002",
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

### 2. 上传文档

**接口**: `POST /knowledge/{kb_id}/upload`

**请求**: multipart/form-data
- file: 文件对象

### 3. 搜索知识库

**接口**: `POST /knowledge/{kb_id}/search`

**请求体**:
```json
{
  "query": "如何使用FastAPI？",
  "top_k": 5
}
```

**响应**:
```json
[
  {
    "content": "文档内容片段...",
    "metadata": {
      "title": "FastAPI教程",
      "chunk_index": 0
    },
    "distance": 0.15
  }
]
```

## 接口管理

### 1. 创建自定义接口

**接口**: `POST /interfaces`

**请求体示例 - API类型**:
```json
{
  "name": "获取天气",
  "description": "获取城市天气信息",
  "type": "api",
  "config": {
    "url": "https://api.weather.com/v1/current",
    "method": "GET",
    "headers": {
      "Authorization": "Bearer xxx"
    },
    "param_mapping": {
      "city": "location"
    }
  },
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "城市名称"
      }
    }
  }
}
```

**请求体示例 - 函数类型**:
```json
{
  "name": "计算器",
  "description": "执行简单计算",
  "type": "function",
  "code": "def main(a, b, op):\n    if op == 'add':\n        return a + b\n    elif op == 'sub':\n        return a - b\n    return None",
  "parameters": {
    "type": "object",
    "properties": {
      "a": {"type": "number"},
      "b": {"type": "number"},
      "op": {"type": "string", "enum": ["add", "sub"]}
    }
  }
}
```

### 2. 执行接口

**接口**: `POST /interfaces/{interface_id}/execute`

**请求体**:
```json
{
  "parameters": {
    "a": 10,
    "b": 5,
    "op": "add"
  }
}
```

## 对话接口

### 1. 创建对话

**接口**: `POST /chat/conversations`

**请求体**:
```json
{
  "title": "技术咨询",
  "knowledge_base_id": "kb_uuid",
  "system_prompt": "你是一个专业的技术顾问",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### 2. 发送消息

**接口**: `POST /chat/conversations/{conversation_id}/messages`

**请求体**:
```json
{
  "message": "什么是FastAPI？",
  "stream": false,
  "use_knowledge_base": true
}
```

**响应**:
```json
{
  "role": "assistant",
  "content": "FastAPI是一个现代、快速的Web框架..."
}
```

### 3. 流式响应

设置 `stream: true` 可获得流式响应（Server-Sent Events）:

```
data: {"content": "Fast"}
data: {"content": "API"}
data: {"content": "是"}
...
data: {"done": true}
```

### 4. 获取对话历史

**接口**: `GET /chat/conversations/{conversation_id}/messages`

## 错误处理

所有错误响应格式:

```json
{
  "detail": "错误描述信息"
}
```

常见HTTP状态码:
- 200: 成功
- 400: 请求参数错误
- 401: 未授权
- 404: 资源不存在
- 500: 服务器内部错误

## 限流

API限流规则:
- 普通接口: 100请求/分钟
- 对话接口: 20请求/分钟
- 文件上传: 10请求/分钟

## 完整API文档

启动服务后访问:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

