# LLM配置指南

## 概述

CoreMind支持多种LLM提供商，本文档详细说明如何配置各种LLM服务。

## 通用配置步骤

1. 进入 **LLM配置** 页面 (`/llm-configs`)
2. 点击 **添加LLM配置**
3. 填写配置信息：
   - 配置名称
   - 选择供应商
   - 选择或输入模型名称
   - 填写API密钥
   - 配置API基础URL（可选）
   - 设置温度参数和最大Token数
4. 点击 **确定** 保存

> ⚠️ **安全提示**：系统会使用 `ENCRYPTION_KEY` 对 API 密钥进行加密存储。请在部署环境的 `.env` 文件中设置自定义的 `ENCRYPTION_KEY`（使用 `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` 生成），以免重启后无法解密已有密钥。

## 各提供商配置说明

### 1. OpenAI (GPT-3.5/4)

**获取API密钥：**
- 访问 https://platform.openai.com/api-keys
- 创建新的API密钥（格式：`sk-xxx`）

**配置示例：**
```
配置名称: GPT-4主力模型
供应商: OpenAI (GPT-3.5/4)
模型名称: gpt-4o
API密钥: sk-proj-xxxxxxxxxxxxx
API基础URL: https://api.openai.com/v1（默认，可不填）
温度: 0.7
最大Token: 4000
```

**常见错误：**
- **401 Unauthorized**: API密钥错误或已过期
- **429 Too Many Requests**: 请求频率过高或余额不足

---

### 2. 阿里云通义千问

**获取API密钥：**
- 访问 https://dashscope.console.aliyun.com/
- 创建API密钥（格式：`sk-xxx`）

**API模式说明：**

阿里云通义千问支持两种API模式：

#### 模式1：兼容模式（推荐）

使用类似OpenAI的API格式，更简单易用。

**配置示例：**
```
配置名称: 通义千问Max
供应商: 阿里云通义千问
模型名称: qwen-max
API密钥: sk-xxxxxxxxxxxxx
API基础URL: https://dashscope.aliyuncs.com/compatible-mode/v1（默认）
温度: 0.7
最大Token: 2000
```

#### 模式2：旧版API

使用阿里云原生API格式。

**配置示例：**
```
配置名称: 通义千问Plus
供应商: 阿里云通义千问
模型名称: qwen-plus
API密钥: sk-xxxxxxxxxxxxx
API基础URL: https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation
温度: 0.7
最大Token: 2000
```

**常见错误：**

- **401 Unauthorized**: 
  - API密钥格式错误（应为 `sk-xxx`）
  - API密钥未激活
  - API密钥权限不足
  
  **解决方法：**
  1. 检查API密钥是否正确复制（注意前后空格）
  2. 登录阿里云控制台确认密钥状态
  3. 确认密钥有调用通义千问的权限

- **403 Forbidden**: 
  - 账户余额不足
  - 模型访问权限不足

---

### 3. DeepSeek

**获取API密钥：**
- 访问 https://platform.deepseek.com/
- 创建API密钥

**配置示例：**
```
配置名称: DeepSeek Chat
供应商: DeepSeek
模型名称: deepseek-chat
API密钥: sk-xxxxxxxxxxxxx
API基础URL: https://api.deepseek.com/v1（默认）
温度: 0.7
最大Token: 4000
```

---

### 4. 智谱AI (ChatGLM)

**获取API密钥：**
- 访问 https://open.bigmodel.cn/
- 创建API密钥

**配置示例：**
```
配置名称: ChatGLM-4
供应商: 智谱AI (ChatGLM)
模型名称: glm-4-plus
API密钥: xxxxxxxxxxxxxx
API基础URL: https://open.bigmodel.cn/api/paas/v4（默认）
温度: 0.7
最大Token: 2000
```

---

### 5. 月之暗面 (Kimi)

**获取API密钥：**
- 访问 https://platform.moonshot.cn/
- 创建API密钥

**配置示例：**
```
配置名称: Kimi Chat
供应商: 月之暗面 (Kimi)
模型名称: moonshot-v1-8k
API密钥: sk-xxxxxxxxxxxxx
API基础URL: https://api.moonshot.cn/v1（默认）
温度: 0.7
最大Token: 8000
```

---

### 6. Ollama (本地部署)

**前置条件：**
- 本地已安装并运行Ollama
- 已下载所需模型（如：`ollama pull llama3.2`）

**配置示例：**
```
配置名称: 本地Llama3
供应商: Ollama (本地部署)
模型名称: llama3.2
API密钥: （留空，本地部署不需要）
API基础URL: http://localhost:11434（默认）
温度: 0.7
最大Token: 2000
```

**启动Ollama：**
```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull llama3.2

# 启动服务（通常自动启动）
ollama serve
```

---

### 7. 自定义模型

**适用场景：**
- 使用其他兼容OpenAI API格式的LLM服务
- 企业内部部署的LLM服务

**配置示例：**
```
配置名称: 企业内网GPT
供应商: 自定义
模型名称: gpt-4-enterprise
API密钥: sk-xxxxxxxxxxxxx
API基础URL: https://llm.internal.company.com/v1
温度: 0.7
最大Token: 4000
```

**要求：**
- API格式需兼容OpenAI Chat Completions API
- 支持Bearer Token认证

---

## 错误排查

### 通用排查步骤

1. **检查API密钥**
   - 确认密钥格式正确
   - 确认密钥已激活
   - 确认密钥有足够权限

2. **检查网络连接**
   - 测试能否访问API服务地址
   - 检查防火墙设置
   - 检查代理配置

3. **检查配置信息**
   - 确认模型名称正确
   - 确认API基础URL正确
   - 确认参数范围合理（温度0-2，Token数>0）

4. **查看错误信息**
   - 系统会显示详细的错误信息
   - 根据错误提示进行排查

### 常见错误码

| 错误码 | 含义 | 解决方法 |
|--------|------|----------|
| 401 | 未授权 | 检查API密钥是否正确 |
| 403 | 禁止访问 | 检查权限和余额 |
| 404 | 资源不存在 | 检查模型名称和URL |
| 429 | 请求过多 | 降低请求频率或等待 |
| 500 | 服务器错误 | 稍后重试或联系服务商 |

---

## 最佳实践

### 1. API密钥安全

- ✅ **不要**在代码中硬编码API密钥
- ✅ **不要**将API密钥提交到Git仓库
- ✅ 使用环境变量或加密存储
- ✅ 定期轮换API密钥

### 2. 成本控制

- 设置合理的 `max_tokens` 限制
- 监控API调用量
- 使用本地模型（Ollama）进行开发测试

### 3. 性能优化

- 根据场景选择合适的模型
- 调整温度参数（0.7适合对话，0.1适合任务）
- 使用流式输出（待实现）

### 4. 错误处理

- 配置多个LLM作为备用
- 实现重试机制（待实现）
- 记录错误日志便于排查

---

## 测试配置

配置完成后，建议进行测试：

1. **创建助手配置**
   - 选择刚配置的LLM
   - 创建测试助手

2. **创建对话**
   - 使用测试助手创建对话
   - 发送测试消息

3. **验证功能**
   - 确认能正常收到回复
   - 检查回复质量
   - 验证参数是否生效

---

## 获取帮助

如遇到问题：

1. 查看错误信息中的详细提示
2. 检查本文档的常见错误部分
3. 查看后端日志：`tail -f backend/backend.log`
4. 查看API文档：http://localhost:8000/docs

---

**最后更新：** 2025-11-12

