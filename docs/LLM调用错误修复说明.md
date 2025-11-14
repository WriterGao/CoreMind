# LLM调用错误修复说明

## 问题描述

用户在使用阿里云通义千问时遇到 **401 Unauthorized** 错误：

```
抱歉, LLM调用失败: Client error '401 Unauthorized' for url 
'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
```

## 问题原因

1. **API模式不匹配**：阿里云通义千问支持两种API模式
   - **兼容模式**：`/compatible-mode/v1/chat/completions`（类似OpenAI格式）
   - **旧版API**：`/api/v1/services/aigc/text-generation/generation`（阿里云原生格式）
   
   原代码没有正确识别和处理兼容模式。

2. **错误处理不完善**：错误信息不够友好，用户难以快速定位问题。

## 修复内容

### 1. 修复阿里云通义千问API调用

**文件：** `backend/app/services/llm_service.py`

**改进：**
- ✅ 自动识别兼容模式和旧版API
- ✅ 根据API模式使用正确的请求格式
- ✅ 支持两种响应格式的解析
- ✅ 改进错误处理，提供详细的错误信息

**代码逻辑：**
```python
# 判断使用兼容模式还是旧版API
if self.api_base:
    if "compatible-mode" in self.api_base:
        # 兼容模式：类似OpenAI格式
        url = f"{self.api_base.rstrip('/')}/chat/completions"
        request_data = {
            "model": self.model_name,
            "messages": messages,  # 直接使用OpenAI格式
            ...
        }
    else:
        # 旧版API格式
        url = f"{self.api_base}/api/v1/services/aigc/text-generation/generation"
        request_data = {
            "model": self.model_name,
            "input": {"messages": qwen_messages},  # 阿里云格式
            ...
        }
else:
    # 默认使用兼容模式
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
```

### 2. 改进错误处理

**改进内容：**
- ✅ 针对401错误提供详细的排查建议
- ✅ 针对403错误提供权限和余额检查提示
- ✅ 针对网络错误提供连接检查提示
- ✅ 解析并显示API返回的具体错误信息

**错误信息示例：**
```
API密钥认证失败（401 Unauthorized）。
请检查：
1. API密钥是否正确（格式：sk-xxx）
2. API密钥是否已激活
3. API密钥是否有足够的权限
```

### 3. 更新默认配置

**文件：** `backend/app/api/llm_config.py`

**改进：**
- ✅ 将阿里云通义千问的默认API基础URL更新为兼容模式
- ✅ 从 `https://dashscope.aliyuncs.com/api/v1` 
- ✅ 更新为 `https://dashscope.aliyuncs.com/compatible-mode/v1`

### 4. 改进其他LLM提供商的错误处理

**改进内容：**
- ✅ OpenAI：添加401和429错误处理
- ✅ DeepSeek：添加401错误处理
- ✅ 统一错误信息格式

## 配置建议

### 阿里云通义千问配置

**推荐配置（兼容模式）：**
```
供应商: 阿里云通义千问
模型名称: qwen-max
API密钥: sk-xxxxxxxxxxxxx（从阿里云控制台获取）
API基础URL: https://dashscope.aliyuncs.com/compatible-mode/v1（默认）
温度: 0.7
最大Token: 2000
```

**旧版API配置（如需要）：**
```
供应商: 阿里云通义千问
模型名称: qwen-plus
API密钥: sk-xxxxxxxxxxxxx
API基础URL: https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation
温度: 0.7
最大Token: 2000
```

## 验证修复

### 测试步骤

1. **更新LLM配置**
   - 进入LLM配置页面
   - 编辑阿里云通义千问配置
   - 确认API基础URL为：`https://dashscope.aliyuncs.com/compatible-mode/v1`
   - 确认API密钥正确

2. **测试调用**
   - 创建或使用现有助手配置
   - 创建对话并发送消息
   - 验证是否能正常收到回复

3. **错误测试**
   - 故意输入错误的API密钥
   - 验证错误信息是否友好清晰

### 预期结果

✅ **成功情况：**
- 能够正常调用API
- 收到AI回复

✅ **错误情况：**
- 显示友好的错误信息
- 提供具体的排查建议
- 帮助用户快速定位问题

## 相关文档

- [LLM配置指南](./LLM配置指南.md) - 详细的LLM配置说明
- [开发规范](./开发规范.md) - 代码开发规范

## 更新日志

**2025-11-12**
- ✅ 修复阿里云通义千问兼容模式API调用
- ✅ 改进所有LLM提供商的错误处理
- ✅ 更新默认API基础URL
- ✅ 添加详细的错误提示信息

---

**修复完成！** 请重新测试LLM调用功能。

