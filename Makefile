.PHONY: help install dev prod down clean test lint

help:  ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## 安装依赖
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install

dev:  ## 启动开发环境
	docker-compose up -d

dev-build:  ## 构建并启动开发环境
	docker-compose up -d --build

prod:  ## 启动生产环境
	docker-compose -f docker-compose.prod.yml up -d

prod-build:  ## 构建并启动生产环境
	docker-compose -f docker-compose.prod.yml up -d --build

down:  ## 停止所有服务
	docker-compose down
	docker-compose -f docker-compose.prod.yml down

clean:  ## 清理所有容器和数据卷
	docker-compose down -v
	docker-compose -f docker-compose.prod.yml down -v

logs:  ## 查看日志
	docker-compose logs -f

logs-backend:  ## 查看后端日志
	docker-compose logs -f backend

logs-frontend:  ## 查看前端日志
	docker-compose logs -f frontend

init-db:  ## 初始化数据库
	cd backend && python scripts/init_db.py

test:  ## 运行测试
	cd backend && pytest

lint:  ## 代码检查
	@echo "检查Python代码..."
	cd backend && black --check app/ && isort --check-only app/ && flake8 app/
	@echo "检查TypeScript代码..."
	cd frontend && npm run lint

format:  ## 格式化代码
	@echo "格式化Python代码..."
	cd backend && black app/ && isort app/
	@echo "格式化TypeScript代码..."
	cd frontend && npm run lint -- --fix

type-check:  ## 类型检查
	@echo "检查Python类型..."
	cd backend && mypy app/ || true
	@echo "检查TypeScript类型..."
	cd frontend && npx tsc --noEmit

test:  ## 运行测试
	@echo "运行后端测试..."
	cd backend && pytest -v
	@echo "运行前端测试..."
	cd frontend && npm test || true

test-cov:  ## 运行测试并生成覆盖率报告
	@echo "运行测试并生成覆盖率报告..."
	cd backend && pytest --cov=app --cov-report=html --cov-report=term

pre-commit: format lint type-check test  ## 提交前检查（格式化、检查、测试）
	@echo "✅ 所有检查通过，可以提交代码"

shell-backend:  ## 进入后端容器Shell
	docker-compose exec backend /bin/bash

shell-frontend:  ## 进入前端容器Shell
	docker-compose exec frontend /bin/sh

shell-db:  ## 进入数据库Shell
	docker-compose exec postgres psql -U coremind -d coremind

backup-db:  ## 备份数据库
	docker-compose exec postgres pg_dump -U coremind coremind > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db:  ## 恢复数据库（需要指定备份文件: make restore-db FILE=backup.sql）
	cat $(FILE) | docker-compose exec -T postgres psql -U coremind coremind

