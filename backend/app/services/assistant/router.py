"""
智能路由服务
根据用户问题自动判断应该使用知识库、数据库查询还是接口调用
"""
import re
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.assistant_config import AssistantConfig
from app.models.datasource import DataSource
from app.models.knowledge import KnowledgeBase
from app.models.interface import CustomInterface


class QueryRouter:
    """查询路由器"""
    
    # 知识库关键词
    KNOWLEDGE_KEYWORDS = [
        "什么是", "介绍", "解释", "说明", "概念", "定义",
        "怎么样", "如何", "为什么", "原理", "背景",
        "文档", "资料", "信息", "内容", "知识"
    ]
    
    # 数据查询关键词
    DATA_KEYWORDS = [
        "查询", "统计", "数量", "多少", "几个", "列表",
        "数据", "记录", "条目", "信息", "详情",
        "最新", "最近", "历史", "时间", "日期",
        "用户", "订单", "产品", "客户", "商品"
    ]
    
    # 接口调用关键词
    INTERFACE_KEYWORDS = [
        "调用", "执行", "运行", "处理", "操作",
        "创建", "新建", "添加", "插入",
        "修改", "更新", "编辑", "改变",
        "删除", "移除", "清除",
        "发送", "提交", "上传", "下载"
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def route_query(
        self,
        query: str,
        assistant_config: AssistantConfig
    ) -> Dict[str, any]:
        """
        路由查询到合适的服务
        
        Args:
            query: 用户查询
            assistant_config: 助手配置
            
        Returns:
            路由结果: {
                "route_type": "knowledge_base" | "datasource" | "interface" | "mixed",
                "confidence": 0.0-1.0,
                "services": [...],
                "reason": "路由原因"
            }
        """
        # 如果未启用自动路由，返回所有可用服务
        if not assistant_config.auto_route:
            return {
                "route_type": "mixed",
                "confidence": 1.0,
                "services": self._get_all_services(assistant_config),
                "reason": "自动路由未启用，使用所有可用服务"
            }
        
        # 计算各类型的匹配分数
        knowledge_score = self._calculate_score(query, self.KNOWLEDGE_KEYWORDS)
        data_score = self._calculate_score(query, self.DATA_KEYWORDS)
        interface_score = self._calculate_score(query, self.INTERFACE_KEYWORDS)
        
        # 获取最高分数及对应类型
        max_score = max(knowledge_score, data_score, interface_score)
        
        # 如果分数太低，使用混合模式
        if max_score < 0.3:
            return {
                "route_type": "mixed",
                "confidence": 0.5,
                "services": self._get_all_services(assistant_config),
                "reason": "无法明确判断查询意图，使用所有可用服务"
            }
        
        # 根据最高分数确定路由类型
        if knowledge_score == max_score and assistant_config.enable_knowledge_base:
            return {
                "route_type": "knowledge_base",
                "confidence": knowledge_score,
                "services": self._get_knowledge_bases(assistant_config),
                "reason": "检测到知识查询意图，使用知识库检索"
            }
        elif data_score == max_score and assistant_config.enable_datasource:
            return {
                "route_type": "datasource",
                "confidence": data_score,
                "services": self._get_datasources(assistant_config),
                "reason": "检测到数据查询意图，使用数据源查询"
            }
        elif interface_score == max_score and assistant_config.enable_interface:
            return {
                "route_type": "interface",
                "confidence": interface_score,
                "services": self._get_interfaces(assistant_config),
                "reason": "检测到操作执行意图，使用接口调用"
            }
        else:
            # 如果首选服务未启用，使用混合模式
            return {
                "route_type": "mixed",
                "confidence": max_score * 0.7,
                "services": self._get_all_services(assistant_config),
                "reason": "首选服务未启用，使用其他可用服务"
            }
    
    def _calculate_score(self, query: str, keywords: List[str]) -> float:
        """计算查询与关键词的匹配分数"""
        query_lower = query.lower()
        matches = sum(1 for keyword in keywords if keyword in query_lower)
        
        # 基础分数
        score = matches / len(keywords)
        
        # 如果有多个关键词匹配，提高分数
        if matches >= 2:
            score = min(score * 1.5, 1.0)
        
        return score
    
    def _get_knowledge_bases(self, assistant_config: AssistantConfig) -> List[Dict]:
        """获取可用的知识库"""
        if not assistant_config.knowledge_base_ids:
            return []
        
        knowledge_bases = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.id.in_(assistant_config.knowledge_base_ids),
            KnowledgeBase.is_active == True
        ).all()
        
        return [
            {
                "type": "knowledge_base",
                "id": str(kb.id),
                "name": kb.name,
                "description": kb.description
            }
            for kb in knowledge_bases
        ]
    
    def _get_datasources(self, assistant_config: AssistantConfig) -> List[Dict]:
        """获取可用的数据源"""
        if not assistant_config.datasource_ids:
            return []
        
        datasources = self.db.query(DataSource).filter(
            DataSource.id.in_(assistant_config.datasource_ids),
            DataSource.is_active == True
        ).all()
        
        return [
            {
                "type": "datasource",
                "id": str(ds.id),
                "name": ds.name,
                "description": ds.description,
                "datasource_type": ds.type.value,
                "usage_doc": ds.usage_doc,
                "schema_info": ds.schema_info,
                "examples": ds.examples
            }
            for ds in datasources
        ]
    
    def _get_interfaces(self, assistant_config: AssistantConfig) -> List[Dict]:
        """获取可用的接口"""
        if not assistant_config.interface_ids:
            return []
        
        interfaces = self.db.query(CustomInterface).filter(
            CustomInterface.id.in_(assistant_config.interface_ids),
            CustomInterface.is_active == True
        ).all()
        
        return [
            {
                "type": "interface",
                "id": str(intf.id),
                "name": intf.name,
                "description": intf.description,
                "interface_type": intf.type.value
            }
            for intf in interfaces
        ]
    
    def _get_all_services(self, assistant_config: AssistantConfig) -> List[Dict]:
        """获取所有可用服务"""
        services = []
        
        if assistant_config.enable_knowledge_base:
            services.extend(self._get_knowledge_bases(assistant_config))
        
        if assistant_config.enable_datasource:
            services.extend(self._get_datasources(assistant_config))
        
        if assistant_config.enable_interface:
            services.extend(self._get_interfaces(assistant_config))
        
        return services
    
    def enhance_prompt_with_context(
        self,
        query: str,
        route_result: Dict,
        assistant_config: AssistantConfig
    ) -> str:
        """
        根据路由结果增强提示词
        
        Args:
            query: 用户查询
            route_result: 路由结果
            assistant_config: 助手配置
            
        Returns:
            增强后的提示词
        """
        base_prompt = assistant_config.system_prompt or "你是一个AI助手。"
        
        # 添加路由信息
        route_info = f"\n\n【路由信息】\n- 查询类型: {route_result['route_type']}\n- 置信度: {route_result['confidence']:.2f}\n- 原因: {route_result['reason']}\n"
        
        # 添加可用服务信息
        if route_result["services"]:
            route_info += "\n【可用服务】\n"
            for service in route_result["services"]:
                route_info += f"- {service['name']} ({service['type']})"
                if service.get('description'):
                    route_info += f": {service['description']}"
                route_info += "\n"
                
                # 如果是数据源，添加使用规范
                if service['type'] == 'datasource':
                    if service.get('usage_doc'):
                        route_info += f"  使用规范: {service['usage_doc']}\n"
                    if service.get('schema_info'):
                        route_info += f"  结构信息: {service['schema_info']}\n"
                    if service.get('examples'):
                        route_info += f"  使用示例: {service['examples']}\n"
        
        # 添加使用指导
        if route_result["route_type"] == "knowledge_base":
            route_info += "\n请基于知识库中的信息回答问题。如果知识库中没有相关信息，请明确告知用户。"
        elif route_result["route_type"] == "datasource":
            route_info += "\n请根据数据源的使用规范构造查询。返回查询结果前，请先解释你的查询逻辑。"
        elif route_result["route_type"] == "interface":
            route_info += "\n请根据接口定义构造调用参数。执行操作前，请先确认用户意图。"
        else:
            route_info += "\n请综合使用可用服务来回答问题或执行操作。"
        
        return base_prompt + route_info + f"\n\n【用户问题】\n{query}"

