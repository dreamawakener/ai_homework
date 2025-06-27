#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学术诚信检查器 - 现代化GUI版本
美化界面设计，命令行交互模式
"""

import sys
import subprocess
import threading
import os
from datetime import datetime
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QPushButton, QLabel, QFrame, QSpacerItem, 
    QSizePolicy, QGraphicsDropShadowEffect, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QBrush

# 导入原有的功能模块
import re
import time
import json
from typing import Dict, List, Optional, Tuple, Union
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
import openai

# 导入配置管理
from config import get_api_key, get_base_url, get_model_name

my_api_key = get_api_key()
my_base_url = get_base_url()
my_model_name = get_model_name()

# 导入原有的核心类
class AcademicIntegrityChecker:
    """学术诚信检查器，用于识别违反学术诚信的请求"""
    
    def __init__(self):
        # 违反学术诚信的关键词和短语
        self.violation_patterns = [
            # 直接生成全文相关
            r'(帮我|替我|给我)?(写|生成|创建)(一篇|完整的?|全部的?)(论文|研究报告|学术论文)',
            r'(代写|代做|帮写)(论文|作业|研究报告)',
            r'(完整的?|整篇|全文)(论文|研究报告).*生成',
            r'从头.*写.*论文',
            r'写.*完整.*论文',
            
            # 抄袭相关
            r'(复制|抄袭|照搬).*论文',
            r'(改写|重写).*别人.*论文',
            r'(洗稿|换句话说).*论文',
            
            # 学术欺诈相关
            r'(伪造|编造|虚构)(数据|实验结果|引用)',
            r'(假的|虚假的)(实验|数据|结果)',
            r'(编造|杜撰)(参考文献|引用|实验)',
            
            # 直接要求答案
            r'(直接给|告诉我)(答案|结论|结果)',
            r'帮我.*解决.*所有.*问题',
        ]
        
        # 允许的学术协助请求
        self.allowed_patterns = [
            r'(润色|优化|改进|修改)(语言|表达|句子)',
            r'(扩写|扩展|丰富)(段落|章节|内容)',
            r'(总结|概括|提炼)(内容|要点|观点)',
            r'(检查|修正)(语法|拼写|格式)',
            r'(翻译|英文润色)',
            r'(学术写作|写作技巧|论文结构).*建议',
            r'(引用格式|参考文献格式)',
        ]
    
    def check_request(self, request: str) -> Tuple[bool, Optional[str]]:
        """
        使用正则表达式检查请求是否违反学术诚信
        
        Args:
            request: 用户请求内容
            
        Returns:
            Tuple[bool, Optional[str]]: (是否违反, 违反原因)
        """
        request_lower = request.lower()
        
        # 检查是否匹配违反学术诚信的模式
        for pattern in self.violation_patterns:
            if re.search(pattern, request_lower):
                return True, "检测到可能违反学术诚信的请求"
        
        # 检查请求长度和内容复杂度（防止要求生成大量内容）
        if len(request) > 1000 and any(keyword in request_lower for keyword in 
                                      ['写', '生成', '创建', '完成', '帮我做']):
            return True, "请求内容过于复杂，可能涉及代写"
        
        return False, None
    
    def ai_check_request(self, request: str, client, model_name: str) -> Tuple[bool, Optional[str]]:
        """
        使用大模型分析请求是否违反学术诚信
        
        Args:
            request: 用户请求内容
            client: OpenAI兼容客户端
            model_name: 模型名称
            
        Returns:
            Tuple[bool, Optional[str]]: (是否违反, 违反原因)
        """
        system_prompt = """你是一个学术诚信检查专家。请分析用户的请求是否违反学术诚信原则。

学术诚信违规包括但不限于：
1. 代写完整论文、作业或研究报告
2. 生成大量原创学术内容（超过几个段落）
3. 抄袭、洗稿或直接复制他人作品
4. 编造实验数据、引用或研究结果
5. 要求直接提供标准答案而非指导

合法的学术协助包括：
1. 语言润色和表达优化
2. 基于已有内容的扩写建议
3. 内容总结和要点提炼
4. 学术写作技巧指导
5. 格式规范建议

请用JSON格式回复：
{
    "is_violation": true/false,
    "reason": "具体原因",
    "confidence": 0.0-1.0
}"""
        
        try:
            response = client.chat.completions.create(
                model=model_name,  # 使用传入的模型名称
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请分析这个请求：{request}"}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 简单解析JSON结果
            if '"is_violation": true' in result_text:
                # 提取原因
                reason_start = result_text.find('"reason": "') + 11
                reason_end = result_text.find('"', reason_start)
                reason = result_text[reason_start:reason_end] if reason_end > reason_start else "AI检测到违规内容"
                return True, reason
            else:
                return False, None
                
        except Exception as e:
            # AI检查失败时，只依赖正则表达式结果
            print(f"AI检查失败: {e}")
            return False, None
    
    def is_allowed_assistance(self, request: str) -> bool:
        """检查是否为允许的学术协助请求"""
        request_lower = request.lower()
        
        for pattern in self.allowed_patterns:
            if re.search(pattern, request_lower):
                return True
        
        return False


class AcademicWritingAgent:
    """专业论文写作助手Agent，负责具体的学术写作任务"""
    
    def __init__(self, client, model_name: str):
        """
        初始化论文写作Agent
        
        Args:
            client: OpenAI兼容客户端
            model_name: 模型名称
        """
        self.client = client
        self.model = model_name
        self.conversation_history = []
        
        # 专业的论文写作系统提示
        self.system_prompt = """你是一位经验丰富的学术论文写作专家，拥有深厚的学术研究背景和丰富的论文指导经验。

你的核心能力包括：
🎯 **语言润色与优化**
- 提升学术表达的准确性和专业性
- 改进句式结构，增强文章流畅度
- 优化用词选择，符合学术写作规范

📝 **内容扩展与丰富**
- 基于用户提供的要点进行合理扩写
- 补充相关理论背景和研究现状
- 添加逻辑连接，增强论证力度

📋 **结构优化与完善**
- 提供论文章节结构建议
- 优化段落组织和逻辑顺序
- 改善引言、正文、结论的衔接

🔍 **内容分析与总结**
- 提炼文献的核心观点和贡献
- 总结研究方法和主要发现
- 概括论文的创新点和价值

📚 **格式规范与引用**
- 提供APA、MLA、Chicago等引用格式指导
- 规范图表、公式的学术格式
- 完善参考文献列表

⚠️  **重要原则**：
- 严格遵守学术诚信，绝不代写完整论文
- 仅对用户已有内容进行改进和优化
- 提供建设性指导而非直接替代用户思考
- 保持客观中立的学术态度

如果用户给出的内容为中文，则使用中文答复，指解答正文使用中文，解释使用中文；
如果为英文，则使用英文答复，指解答正文使用英文，用中文进行讲解。
请根据用户的具体需求，提供专业、详细、实用的学术写作指导。"""
        
        self.conversation_history.append({"role": "system", "content": self.system_prompt})
    
    def analyze_task_type(self, request: str) -> Dict[str, Union[str, List[str]]]:
        """
        分析用户请求的任务类型
        
        Args:
            request: 用户请求
            
        Returns:
            Dict: 包含任务类型和建议的字典
        """
        task_patterns = {
            "language_polish": ["润色", "优化", "改进", "修改", "表达"],
            "content_expansion": ["扩写", "扩展", "丰富", "详细", "补充"],
            "summarization": ["总结", "概括", "提炼", "摘要"],
            "structure_advice": ["结构", "章节", "组织", "框架", "大纲"],
            "grammar_check": ["语法", "拼写", "格式", "错误"],
            "citation_format": ["引用", "参考文献", "格式", "标注"],
            "translation": ["翻译", "英文", "中文"],
            "writing_guidance": ["写作", "技巧", "方法", "建议", "指导"]
        }
        
        detected_types = []
        request_lower = request.lower()
        
        for task_type, keywords in task_patterns.items():
            if any(keyword in request_lower for keyword in keywords):
                detected_types.append(task_type)
        
        # 如果没有检测到明确类型，归类为一般写作指导
        if not detected_types:
            detected_types = ["writing_guidance"]
        
        return {
            "task_types": detected_types,
            "primary_type": detected_types[0] if detected_types else "writing_guidance",
            "suggestions": self._get_task_suggestions(detected_types[0] if detected_types else "writing_guidance")
        }
    
    def _get_task_suggestions(self, task_type: str) -> List[str]:
        """根据任务类型提供建议"""
        suggestions_map = {
            "language_polish": [
                "请提供需要润色的具体文本段落",
                "说明希望改进的方向（流畅度、专业性等）",
                "标注您认为有问题的句子或表达"
            ],
            "content_expansion": [
                "提供需要扩写的核心要点或段落",
                "说明扩写的目标长度和深度",
                "明确扩写的重点方向（理论、实例、分析等）"
            ],
            "summarization": [
                "提供需要总结的完整文本",
                "说明总结的目标长度",
                "指明需要重点关注的方面"
            ],
            "structure_advice": [
                "描述论文的主题和研究问题",
                "说明论文类型（实证研究、文献综述等）",
                "提供现有的结构框架或想法"
            ],
            "grammar_check": [
                "提供需要检查的具体文本",
                "说明文本的学科背景",
                "标注您不确定的语法点"
            ],
            "citation_format": [
                "说明需要的引用格式（APA、MLA等）",
                "提供需要格式化的引用信息",
                "明确引用类型（期刊、书籍、网页等）"
            ],
            "translation": [
                "提供需要翻译的原文",
                "说明翻译的学科领域",
                "标注专业术语和关键概念"
            ],
            "writing_guidance": [
                "描述具体的写作困难或问题",
                "说明论文的主题和研究阶段",
                "提供现有的写作内容或想法"
            ]
        }
        
        return suggestions_map.get(task_type, ["请详细描述您的具体需求"])
    
    def process_request(self, request: str, typing_delay: float = 0.001) -> str:
        """
        处理学术写作请求
        
        Args:
            request: 用户请求
            typing_delay: 打字机效果延迟
            
        Returns:
            str: 处理结果
        """
        # 分析任务类型
        task_analysis = self.analyze_task_type(request)
        
        # 构建专业的响应提示
        enhanced_request = f"""
任务分析：
- 主要任务类型：{task_analysis['primary_type']}
- 检测到的任务类型：{', '.join(task_analysis['task_types'])}

用户请求：{request}

请作为专业的学术写作专家，根据任务类型提供详细、实用的指导和帮助。
如果用户提供了具体的文本内容，请对其进行专业的分析和改进建议。
"""
        
        # 添加到对话历史
        self.conversation_history.append({"role": "user", "content": enhanced_request})
        
        try:
            # 创建流式请求
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.7,  # 适中的温度，保持专业性的同时允许一定创造性
                max_tokens=4096,
                stream=True
            )
            
            full_response = ""
            print("📝 论文写作助手: ", end="", flush=True)
            
            # 逐块处理流式响应
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # 打字机效果输出
                    for char in content:
                        sys.stdout.write(char)
                        sys.stdout.flush()
                        time.sleep(typing_delay)
            
            print()
            
            # 将助手响应添加到历史
            self.conversation_history.append({"role": "assistant", "content": full_response})
            
            return full_response
            
        except Exception as e:
            error_msg = f"处理请求时发生错误：{str(e)}"
            print(error_msg)
            return error_msg
    
    def get_writing_tips(self, topic: str = "general") -> str:
        """提供学术写作技巧"""
        tips_request = f"请为'{topic}'主题提供专业的学术写作技巧和建议"
        return self.process_request(tips_request)
    
    def reset_conversation(self):
        """重置对话历史，保留系统提示"""
        self.conversation_history = [self.conversation_history[0]]  # 只保留系统提示


class AcademicWritingAssistant:
    """增强版学术论文写作助手，整合学术诚信检查和专业写作Agent"""
    
    def __init__(self, api_key: str = "", base_url: str = "https://api.siliconflow.cn/v1", 
                 model_name: str = "Pro/deepseek-ai/DeepSeek-V3"):
        """
        初始化写作助手
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model_name: 模型名称
        """
        self.integrity_checker = AcademicIntegrityChecker()
        
        # 初始化OpenAI兼容客户端
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 设置模型名称
        self.model = model_name
        
        # 初始化专业写作Agent
        self.writing_agent = AcademicWritingAgent(self.client, self.model)
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "approved_requests": 0,
            "rejected_requests": 0,
            "task_types": {}
        }
    
    def process_request(self, user_input: str, typing_delay: float = 0.001, 
                       show_progress: bool = True) -> str:
        """
        处理用户请求（完整流程：学术诚信检查 + 专业写作协助）
        
        Args:
            user_input: 用户输入的请求
            typing_delay: 打字机效果延迟
            show_progress: 是否显示处理进度
            
        Returns:
            str: 完整的响应内容
        """
        self.stats["total_requests"] += 1
        
        if show_progress:
            print("🔍 正在进行学术诚信检查...")
        
        # 双重学术诚信检查
        # 1. 正则表达式检查
        is_violation_regex, reason_regex = self.integrity_checker.check_request(user_input)
        
        # 2. AI智能检查
        is_violation_ai, reason_ai = self.integrity_checker.ai_check_request(
            user_input, self.client, self.model
        )
        
        # 如果任一检查发现违规，则拒绝服务
        if is_violation_regex or is_violation_ai:
            self.stats["rejected_requests"] += 1
            violation_reason = reason_ai if reason_ai else reason_regex
            rejection_msg = self._generate_rejection_message(violation_reason)
            
            if show_progress:
                print("❌ 学术诚信检查未通过")
            
            # 流式输出拒绝消息
            print("🚫 学术诚信检查器: ", end="", flush=True)
            
            for char in rejection_msg:
                sys.stdout.write(char)
                sys.stdout.flush()
                time.sleep(typing_delay)
            print()
            
            return rejection_msg
        
        # 检查是否为允许的协助请求
        if not self.integrity_checker.is_allowed_assistance(user_input):
            if self._is_potentially_problematic(user_input):
                self.stats["rejected_requests"] += 1
                rejection_msg = self._generate_rejection_message("请求可能违反学术诚信原则")
                
                if show_progress:
                    print("❌ 请求可能存在问题")
                
                # 流式输出拒绝消息
                print("🚫 学术诚信检查器: ", end="", flush=True)
                
                for char in rejection_msg:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    time.sleep(typing_delay)
                print()
                
                return rejection_msg
        
        if show_progress:
            print("✅ 学术诚信检查通过")
            print("🤖 启动专业论文写作助手...")
        
        # 通过检查，交给专业写作Agent处理
        self.stats["approved_requests"] += 1
        
        # 分析任务类型并更新统计
        task_analysis = self.writing_agent.analyze_task_type(user_input)
        primary_type = task_analysis["primary_type"]
        self.stats["task_types"][primary_type] = self.stats["task_types"].get(primary_type, 0) + 1
        
        # 处理请求
        response = self.writing_agent.process_request(user_input, typing_delay)
        
        return response
    
    def _is_potentially_problematic(self, request: str) -> bool:
        """检查请求是否存在潜在问题"""
        problematic_indicators = [
            len(request.split()) > 200,  # 请求过长
            '帮我完成' in request and '论文' in request,
            '全部' in request and ('写' in request or '做' in request),
            '代替我' in request,
        ]
        
        return any(problematic_indicators)
    
    def _generate_rejection_message(self, reason: str) -> str:
        """生成拒绝服务的消息"""
        return f"""很抱歉，我无法处理您的请求。

🚫 违反学术诚信原则

原因：{reason}

✅ 我可以为您提供以下类型的专业学术写作协助：

📝 **语言润色与优化**
• 改进学术表达的准确性和专业性
• 优化句式结构，增强文章流畅度
• 提升用词选择，符合学术写作规范

📋 **内容扩展与丰富**
• 基于您提供的要点进行合理扩写
• 补充相关理论背景和研究现状
• 添加逻辑连接，增强论证力度

🔍 **内容分析与总结**
• 提炼文献的核心观点和贡献
• 总结研究方法和主要发现
• 概括论文的创新点和价值

📚 **格式规范与引用**
• 提供各种引用格式指导
• 规范图表、公式的学术格式
• 完善参考文献列表

💡 **使用建议**：请提供您已经撰写的具体内容或明确的改进需求，我将为您提供专业的学术写作指导。

学术诚信是研究工作的基石，让我们一起维护良好的学术环境！"""
    
    def get_stats(self) -> Dict:
        """获取使用统计信息"""
        return self.stats.copy()
    
    def reset_agent(self):
        """重置写作Agent的对话历史"""
        self.writing_agent.reset_conversation()
    
    def get_writing_tips(self, topic: str = "general") -> str:
        """获取写作技巧"""
        return self.writing_agent.get_writing_tips(topic)


# 原有功能函数保持不变
def main():
    """主函数示例"""
    # 配置您的API信息
    my_api_key = get_api_key()
    my_base_url = get_base_url()  
    my_model_name = get_model_name()
    
    # 初始化增强版助手
    assistant = AcademicWritingAssistant(
        api_key=my_api_key,
        base_url=my_base_url,
        model_name=my_model_name
    )
    
    print("=== 增强版学术论文写作助手 ===")
    print(f"🤖 使用模型: {my_model_name}")
    print(f"🌐 服务地址: {my_base_url}")
    print("✨ 功能特色：学术诚信检查 + 专业论文写作Agent")
    print("📋 支持：语言润色、内容扩写、结构建议、格式规范等")
    print("\n输入 'quit' 退出程序")
    print("输入 'stats' 查看使用统计")
    print("输入 'tips [主题]' 获取写作技巧")
    print("输入 'reset' 重置对话历史\n")
    
    while True:
        try:
            user_input = input("👤 用户: ")
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                # 显示最终统计
                stats = assistant.get_stats()
                print(f"\n📊 使用统计:")
                print(f"总请求数: {stats['total_requests']}")
                print(f"通过请求: {stats['approved_requests']}")
                print(f"拒绝请求: {stats['rejected_requests']}")
                if stats['task_types']:
                    print("任务类型分布:")
                    for task_type, count in stats['task_types'].items():
                        print(f"  {task_type}: {count}")
                print("👋 再见！")
                break
            
            if user_input.lower() == 'stats':
                stats = assistant.get_stats()
                print(f"\n📊 当前使用统计:")
                print(f"总请求数: {stats['total_requests']}")
                print(f"通过请求: {stats['approved_requests']}")
                print(f"拒绝请求: {stats['rejected_requests']}")
                if stats['task_types']:
                    print("任务类型分布:")
                    for task_type, count in stats['task_types'].items():
                        print(f"  {task_type}: {count}")
                continue
            
            if user_input.lower().startswith('tips'):
                topic = user_input[4:].strip() if len(user_input) > 4 else "general"
                print(f"\n📚 获取'{topic}'相关的写作技巧...")
                assistant.get_writing_tips(topic)
                print("\n" + "="*50 + "\n")
                continue
            
            if user_input.lower() == 'reset':
                assistant.reset_agent()
                print("🔄 对话历史已重置")
                continue
            
            if not user_input.strip():
                continue
            
            print()  # 换行
            
            # 处理请求（包含学术诚信检查和专业写作协助）
            response = assistant.process_request(
                user_input, 
                typing_delay=0.01,  # 可调整打字速度
                show_progress=True
            )
            
            print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 程序已退出")
            break
        except Exception as e:
            print(f"发生错误: {e}")


def demo_test():
    """演示测试函数"""
    my_api_key = get_api_key()
    my_base_url = get_base_url()
    my_model_name = get_model_name()
    
    # 初始化助手
    assistant = AcademicWritingAssistant(
        api_key=my_api_key,
        base_url=my_base_url,
        model_name=my_model_name
    )
    
    # 测试请求
    test_requests = [
        "帮我写一篇关于人工智能的完整论文",  # 违反学术诚信
        """请帮我润色这段话：人工智能技术发展迅速，在各个领域都有应用。特别是在医疗、金融和教育等行业，AI技术正在改变传统的工作方式。""",  # 合法请求
        "请帮我扩写这个观点：深度学习在图像识别中具有显著优势，主要体现在特征提取和模式识别能力上。",  # 合法请求
        "代写一篇5000字的研究报告",  # 违反学术诚信
        """请总结一下这段内容的要点：深度学习是机器学习的一个分支，它模拟人脑神经网络的结构和功能。通过多层神经网络，深度学习能够自动学习数据的特征表示，在图像识别、自然语言处理、语音识别等领域取得了突破性进展。"""  # 合法请求
    ]
    
    print("=== 增强版学术论文写作助手演示 ===")
    print(f"🤖 使用模型: {my_model_name}")
    print(f"🌐 服务地址: {my_base_url}")
    print("✨ 功能特色：学术诚信检查 + 专业论文写作Agent\n")
    
    for i, request in enumerate(test_requests, 1):
        print(f"📝 测试 {i}: {request[:50]}{'...' if len(request) > 50 else ''}")
        print("-" * 70)
        
        response = assistant.process_request(
            request,
            typing_delay=0.005,  # 演示时稍快一些
            show_progress=True
        )
        
        print("\n" + "="*70 + "\n")
    
    # 显示最终统计
    print("📊 演示完成，最终统计:")
    stats = assistant.get_stats()
    print(f"总请求数: {stats['total_requests']}")
    print(f"通过请求: {stats['approved_requests']}")
    print(f"拒绝请求: {stats['rejected_requests']}")
    if stats['task_types']:
        print("任务类型分布:")
        for task_type, count in stats['task_types'].items():
            print(f"  {task_type}: {count}")


def interactive_demo():
    """交互式演示，展示不同功能"""
    
    assistant = AcademicWritingAssistant(
        api_key=my_api_key,
        base_url=my_base_url,
        model_name=my_model_name
    )
    
    print("=== 交互式功能演示 ===")
    print("🎯 本演示将展示不同类型的学术写作协助功能\n")
    
    # 演示场景
    scenarios = [
        {
            "title": "语言润色",
            "description": "优化学术表达，提升文本质量",
            "example": "请帮我润色这段话：机器学习算法在数据分析方面有很好的效果，能够处理大量数据并找出规律。"
        },
        {
            "title": "内容扩写", 
            "description": "基于要点进行合理扩展",
            "example": "请帮我扩写这个观点：卷积神经网络在计算机视觉领域具有重要作用。"
        },
        {
            "title": "结构建议",
            "description": "提供论文结构和组织建议", 
            "example": "我正在写一篇关于自然语言处理的论文，请给我一些结构建议。"
        },
        {
            "title": "内容总结",
            "description": "提炼文本要点和核心观点",
            "example": "请总结这段文字的要点：Transformer模型是一种基于注意力机制的神经网络架构，它在自然语言处理任务中表现出色。该模型摒弃了传统的循环神经网络结构，完全依赖注意力机制来处理序列数据，从而实现了并行计算和更好的长距离依赖建模能力。"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"🎭 场景 {i}: {scenario['title']}")
        print(f"📝 描述: {scenario['description']}")
        print(f"💡 示例请求: {scenario['example']}")
        
        proceed = input("\n是否运行此演示? (y/n): ").lower().strip()
        if proceed == 'y':
            print("\n" + "-"*50)
            assistant.process_request(
                scenario['example'],
                typing_delay=0.01,
                show_progress=True
            )
            print("-"*50 + "\n")
        
        if i < len(scenarios):
            input("按回车键继续下一个演示...")
            print()
    
    print("🎉 所有演示完成！")
    
    # 显示统计信息
    stats = assistant.get_stats()
    print(f"\n📊 演示统计:")
    print(f"总请求数: {stats['total_requests']}")
    print(f"通过请求: {stats['approved_requests']}")
    print(f"拒绝请求: {stats['rejected_requests']}")


class ModernButton(QPushButton):
    """现代化自定义按钮"""
    
    def __init__(self, text, icon_text="", color="#3498db", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.icon_text = icon_text
        self.base_color = color
        self.setupButton()
    
    def setupButton(self):
        """设置按钮样式"""
        self.setMinimumSize(200, 60)
        self.setMaximumSize(300, 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置按钮样式
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.base_color}, stop:1 {self.darken_color(self.base_color)});
                color: white;
                border: none;
                border-radius: 15px;
                font: bold 12px "Microsoft YaHei";
                padding: 15px 20px;
                text-align: center;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.lighten_color(self.base_color)}, stop:1 {self.base_color});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.darken_color(self.base_color)}, stop:1 {self.darken_color(self.base_color, 0.3)});
            }}
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(2, 4)
        self.setGraphicsEffect(shadow)
    
    def darken_color(self, color, factor=0.2):
        """使颜色变暗"""
        color_map = {
            "#3498db": "#2980b9",
            "#e74c3c": "#c0392b",
            "#f39c12": "#e67e22",
            "#9b59b6": "#8e44ad",
            "#1abc9c": "#16a085",
            "#34495e": "#2c3e50"
        }
        return color_map.get(color, color)
    
    def lighten_color(self, color, factor=0.2):
        """使颜色变亮"""
        color_map = {
            "#3498db": "#5dade2",
            "#e74c3c": "#ec7063",
            "#f39c12": "#f8c471",
            "#9b59b6": "#bb8fce",
            "#1abc9c": "#58d68d",
            "#34495e": "#566573"
        }
        return color_map.get(color, color)


class StatusCard(QFrame):
    """状态卡片组件"""
    
    def __init__(self, title, status, icon="🔧", parent=None):
        super().__init__(parent)
        self.title = title
        self.status = status
        self.icon = icon
        self.setupCard()
    
    def setupCard(self):
        """设置卡片样式"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedSize(280, 80)
        
        # 设置卡片样式
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # 创建布局
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        
        # 图标
        icon_label = QLabel(self.icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # 文本区域
        text_layout = QVBoxLayout()
        
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        text_layout.addWidget(title_label)
        
        status_label = QLabel(self.status)
        status_label.setFont(QFont("Microsoft YaHei", 10))
        status_label.setStyleSheet("color: #27ae60;")
        text_layout.addWidget(status_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()


class CommandThread(QThread):
    """命令执行线程"""
    output_received = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, function_name):
        super().__init__()
        self.function_name = function_name
    
    def run(self):
        """执行命令"""
        try:
            if self.function_name == "interactive":
                main()
            elif self.function_name == "demo":
                demo_test()
            elif self.function_name == "showcase":
                interactive_demo()
        except Exception as e:
            self.output_received.emit(f"执行错误: {str(e)}")
        finally:
            self.finished.emit()


class ModernAICWindow(QMainWindow):
    """现代化学术诚信检查器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.command_thread = None
    
    def setupUI(self):
        """设置用户界面"""
        self.setWindowTitle("学术诚信检查器 - 现代化版本")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(900, 600)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5f7fa, stop:1 #c3cfe2);
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)
        
        # 标题区域
        self.createTitleSection(main_layout)
        
        # 状态卡片区域
        # self.createStatusSection(main_layout)
        
        # 功能按钮区域
        self.createButtonSection(main_layout)
        
        # 信息显示区域
        self.createInfoSection(main_layout)
        
        # 底部间隔
        main_layout.addStretch()
    
    def createTitleSection(self, parent_layout):
        """创建标题区域"""
        title_layout = QVBoxLayout()
        title_layout.setSpacing(10)
        
        # 主标题
        title_label = QLabel("🔍 学术诚信检查器")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Microsoft YaHei", 28, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                margin: 15px 0;
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(2, 2)
        title_label.setGraphicsEffect(shadow)
        
        title_layout.addWidget(title_label)
        
        # 副标题
        subtitle = QLabel("AI驱动的学术写作诚信检测与专业写作辅助系统")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Microsoft YaHei", 14))
        subtitle.setStyleSheet("""
            QLabel {
                color: #34495e;
                margin-bottom: 10px;
            }
        """)
        title_layout.addWidget(subtitle)
        
        parent_layout.addLayout(title_layout)
    
    # def createStatusSection(self, parent_layout):
    #     """创建状态显示区域"""
    #     status_layout = QHBoxLayout()
    #     status_layout.setSpacing(20)
        
    #     # API状态卡片
    #     api_status = "✅ 已连接" if all([my_api_key, my_base_url, my_model_name]) else "❌ 未配置"
    #     api_card = StatusCard("API状态", api_status, "🌐")
    #     status_layout.addWidget(api_card)
        
    #     # 模型信息卡片
    #     model_name = my_model_name.split('/')[-1] if my_model_name else "未配置"
    #     model_card = StatusCard("AI模型", model_name, "🤖")
    #     status_layout.addWidget(model_card)
        
    #     # 功能状态卡片
    #     function_card = StatusCard("系统状态", "✅ 就绪", "⚡")
    #     status_layout.addWidget(function_card)
        
    #     status_layout.addStretch()
    #     parent_layout.addLayout(status_layout)
    
    def createButtonSection(self, parent_layout):
        """创建功能按钮区域"""
        # 功能说明
        function_title = QLabel("🎯 选择功能模式")
        function_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        function_title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        function_title.setStyleSheet("color: #2c3e50; margin: 20px 0;")
        parent_layout.addWidget(function_title)
        
        # 按钮网格布局
        button_layout = QGridLayout()
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(50, 20, 50, 20)
        
        # 创建功能按钮
        self.interactive_btn = ModernButton(
            "🎮 交互式对话模式\n智能学术写作助手",
            color="#3498db"
        )
        self.interactive_btn.clicked.connect(self.start_interactive_mode)
        
        self.demo_btn = ModernButton(
            "🚀 自动演示模式\n快速功能展示",
            color="#e74c3c"
        )
        self.demo_btn.clicked.connect(self.start_demo_mode)
        
        self.showcase_btn = ModernButton(
            "✨ 功能展示模式\n分步演示体验",
            color="#f39c12"
        )
        self.showcase_btn.clicked.connect(self.start_showcase_mode)
        
        # 添加按钮到布局
        button_layout.addWidget(self.interactive_btn, 0, 0, Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.demo_btn, 0, 1, Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.showcase_btn, 0, 2, Qt.AlignmentFlag.AlignCenter)
        
        # 创建按钮容器
        button_container = QFrame()
        button_container.setLayout(button_layout)
        button_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                margin: 10px;
                padding: 20px;
            }
        """)
        
        parent_layout.addWidget(button_container)
    
    def createInfoSection(self, parent_layout):
        """创建信息显示区域"""
        info_layout = QVBoxLayout()
        
        # 功能特色标题
        features_title = QLabel("💡 系统特色功能")
        features_title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        features_title.setStyleSheet("color: #2c3e50; margin: 10px 0;")
        info_layout.addWidget(features_title)
        
        # 功能特色列表
        features_text = """
🔍 <b>双重学术诚信检查</b>：正则表达式 + AI智能检测，确保学术规范
📝 <b>专业写作辅助</b>：语言润色、内容扩写、结构优化、格式规范
🤖 <b>智能任务识别</b>：自动分析请求类型，提供针对性建议
⚡ <b>实时流式输出</b>：打字机效果展示，流畅的交互体验
📊 <b>统计分析功能</b>：使用数据跟踪，任务类型分布分析
🎯 <b>多种运行模式</b>：交互对话、自动演示、功能展示三种模式
        """
        
        features_label = QLabel(features_text)
        features_label.setFont(QFont("Microsoft YaHei", 11))
        features_label.setStyleSheet("""
            QLabel {
                color: #34495e;
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 10px;
                padding: 20px;
                line-height: 1.6;
            }
        """)
        features_label.setWordWrap(True)
        info_layout.addWidget(features_label)
        
        parent_layout.addLayout(info_layout)
    
    def start_interactive_mode(self):
        """启动交互式对话模式"""
        self.show_status_message("🎮 启动交互式对话模式...")
        self.run_in_terminal("interactive")
    
    def start_demo_mode(self):
        """启动自动演示模式"""
        self.show_status_message("🚀 启动自动演示模式...")
        self.run_in_terminal("demo")
    
    def start_showcase_mode(self):
        """启动功能展示模式"""
        self.show_status_message("✨ 启动功能展示模式...")
        self.run_in_terminal("showcase")
    
    def run_in_terminal(self, mode):
        """在新终端窗口中运行功能"""
        try:
            # 获取当前脚本路径
            current_script = __file__
            
            # 根据操作系统选择命令
            if sys.platform.startswith('win'):
                # Windows系统
                if mode == "interactive":
                    main()
                    # cmd = f'start cmd /k "python "{current_script}" && python -c "import sys; sys.path.append(\'.\'); from AcademicIntegrityChecker_Modern import main; main()""'
                elif mode == "demo":
                    demo_test()
                    # cmd = f'start cmd /k "python "{current_script}" && python -c "import sys; sys.path.append(\'.\'); from AcademicIntegrityChecker_Modern import demo_test; demo_test()""'
                elif mode == "showcase":
                    interactive_demo()
                    # cmd = f'start cmd /k "python "{current_script}" && python -c "import sys; sys.path.append(\'.\'); from AcademicIntegrityChecker_Modern import interactive_demo; interactive_demo()""'
                
                os.system(cmd)
            else:
                # macOS/Linux系统
                if mode == "interactive":
                    cmd = f"python -c 'from AcademicIntegrityChecker_Modern import main; main()'"
                elif mode == "demo":
                    cmd = f"python -c 'from AcademicIntegrityChecker_Modern import demo_test; demo_test()'"
                elif mode == "showcase":
                    cmd = f"python -c 'from AcademicIntegrityChecker_Modern import interactive_demo; interactive_demo()'"
                
                # 在新终端窗口中运行
                if sys.platform == 'darwin':  # macOS
                    os.system(f"osascript -e 'tell app \"Terminal\" to do script \"{cmd}\"'")
                else:  # Linux
                    os.system(f"gnome-terminal -- bash -c '{cmd}; exec bash'")
            
        except Exception as e:
            self.show_error_message(f"启动失败: {str(e)}")
    
    def show_status_message(self, message):
        """显示状态消息"""
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg.setWindowTitle("系统状态")
        msg.setText(message)
        msg.setInformativeText("程序将在新的终端窗口中运行。\n请查看终端窗口进行交互。")
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def show_error_message(self, message):
        """显示错误消息"""
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        msg.setWindowTitle("错误")
        msg.setText(message)
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg.exec()


class AIC(object):
    """现代化AIC界面类"""
    
    def setupUi(self, MainWindow):
        """设置现代化UI"""
        # 创建现代化窗口实例
        self.modern_window = ModernAICWindow()
        
        # 将现代化窗口的内容复制到主窗口
        MainWindow.setWindowTitle("学术诚信检查器 - 现代化版本")
        MainWindow.resize(1000, 700)
        MainWindow.setMinimumSize(900, 600)
        
        # 设置中央部件为现代化窗口的中央部件
        MainWindow.setCentralWidget(self.modern_window.centralWidget())
        
        # 保持原有的菜单栏和状态栏结构
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1000, 25))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.showMessage(f"学术诚信检查器已就绪 | 用户: default | 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        MainWindow.setStatusBar(self.statusbar)
        
        # 添加菜单项
        self.setup_menu()
    
    def setup_menu(self):
        """设置菜单"""
        # 文件菜单
        file_menu = self.menubar.addMenu("文件(&F)")
        file_menu.addAction("退出", lambda: sys.exit())
        
        # 功能菜单
        function_menu = self.menubar.addMenu("功能(&F)")
        function_menu.addAction("🎮 交互式对话模式", self.modern_window.start_interactive_mode)
        function_menu.addAction("🚀 自动演示模式", self.modern_window.start_demo_mode)
        function_menu.addAction("✨ 功能展示模式", self.modern_window.start_showcase_mode)
        
        # 帮助菜单
        help_menu = self.menubar.addMenu("帮助(&H)")
        help_menu.addAction("关于", self.show_about)
    
    def show_about(self):
        """显示关于对话框"""
        about_text = f"""
        <h2>🔍 学术诚信检查器</h2>
        <p><strong>版本:</strong> 3.0 现代化版本</p>
        <p><strong>发布日期:</strong> 2025-06-27</p>
        <p><strong>开发者:</strong> default</p>
        <p><strong>当前时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h3>✨ 核心功能:</h3>
        <ul>
            <li>🔍 双重学术诚信检查（正则 + AI）</li>
            <li>📝 专业学术写作辅助</li>
            <li>🤖 智能任务类型识别</li>
            <li>⚡ 实时流式输出体验</li>
            <li>📊 使用统计与分析</li>
            <li>🎯 多种交互模式</li>
        </ul>
        
        <h3>🏗️ 技术特点:</h3>
        <ul>
            <li>🎨 现代化PyQt6界面设计</li>
            <li>🖥️ 命令行交互模式</li>
            <li>🔗 OpenAI API集成</li>
            <li>🧵 多线程处理架构</li>
            <li>💡 智能UI组件</li>
        </ul>
        
        <p><em>维护学术诚信，提升写作质量！</em></p>
        """
        
        QtWidgets.QMessageBox.about(None, "关于学术诚信检查器", about_text)
    
    def retranslateUi(self, MainWindow):
        """重新翻译UI（保持兼容性）"""
        pass
    
    def on_item_clicked(self, item):
        """点击项目事件（保持兼容性）"""
        pass


def main_gui():
    """启动GUI主程序"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("学术诚信检查器")
    app.setApplicationVersion("3.0 现代化版本")
    app.setOrganizationName("Academic Tools")
    
    # 设置全局样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = QMainWindow()
    ui = AIC()
    ui.setupUi(window)
    
    window.show()
    
    print("🚀 学术诚信检查器现代化版本启动成功！")
    print("🎨 界面特色:")
    print("   - 现代化PyQt6界面设计")
    print("   - 去除输入输出文本框")
    print("   - 命令行交互模式")
    print("   - 美化的按钮和状态卡片")
    print("   - 流畅的动画效果")
    print("   - 智能阴影和渐变")
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"💥 程序运行错误: {e}")


if __name__ == "__main__":
    # 如果直接运行此脚本，则启动GUI
    main_gui()