#!/bin/bash

echo "🚀 CoreMind 前端启动脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 进入前端目录
cd "$(dirname "$0")/frontend"

echo "📍 当前目录: $(pwd)"
echo ""

# 检查node_modules
if [ ! -d "node_modules" ] || [ $(ls node_modules | wc -l) -lt 10 ]; then
    echo "📦 检测到依赖未安装或不完整，开始安装..."
    echo "⚠️  如果遇到权限错误，请先运行:"
    echo "   sudo chown -R $(whoami) ~/.npm"
    echo ""
    
    # 清理旧的安装
    rm -rf node_modules package-lock.json
    
    # 安装依赖
    npm install
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ 依赖安装失败！"
        echo ""
        echo "请手动修复npm缓存权限:"
        echo "   sudo chown -R $(whoami) ~/.npm"
        echo ""
        echo "然后重新运行此脚本"
        exit 1
    fi
fi

echo ""
echo "✅ 依赖检查完成"
echo ""
echo "🚀 启动开发服务器..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "前端将在 http://localhost:5173 启动"
echo "按 Ctrl+C 停止服务"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 启动开发服务器
npm run dev

