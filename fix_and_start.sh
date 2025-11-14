#!/bin/bash

echo "🔧 CoreMind 前端修复和启动脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查是否有sudo权限
echo "📋 步骤1: 修复npm权限（需要输入密码）"
echo "正在执行: sudo chown -R $(whoami) ~/.npm"
echo ""
sudo chown -R $(whoami) ~/.npm

if [ $? -ne 0 ]; then
    echo "❌ 权限修复失败"
    exit 1
fi

echo "✅ 权限修复成功"
echo ""

# 进入前端目录
cd "$(dirname "$0")/frontend"
echo "📍 当前目录: $(pwd)"
echo ""

# 清理旧的安装
echo "📋 步骤2: 清理旧的依赖"
rm -rf node_modules package-lock.json .vite
echo "✅ 清理完成"
echo ""

# 安装依赖
echo "📋 步骤3: 安装前端依赖（这可能需要2-3分钟）"
npm install

if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi

echo "✅ 依赖安装成功"
echo ""

# 启动服务
echo "📋 步骤4: 启动开发服务器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 前端将在以下地址启动:"
echo "   http://localhost:5173"
echo ""
echo "💡 使用提示:"
echo "   - 按 Ctrl+C 停止服务"
echo "   - 保持此窗口打开"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

npm run dev

