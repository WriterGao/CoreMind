-- 为conversations表添加assistant_id字段
-- 这个脚本用于升级数据库以支持助手配置

ALTER TABLE conversations 
ADD COLUMN assistant_id UUID;

-- 添加外键约束
ALTER TABLE conversations 
ADD CONSTRAINT fk_conversations_assistant_id 
FOREIGN KEY (assistant_id) 
REFERENCES assistant_configs(id) 
ON DELETE SET NULL;

-- 添加索引以提高查询性能
CREATE INDEX idx_conversations_assistant_id 
ON conversations(assistant_id);

-- 添加注释
COMMENT ON COLUMN conversations.assistant_id IS '关联的助手配置ID';

