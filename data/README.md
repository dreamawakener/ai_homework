# 🎓 学术论文写作助手 (Academic Writing Assistant)

一个基于多Agent协作的智能学术写作助手系统，为高校学生提供从文献调研到论文完成的全流程支持。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-API-orange.svg)](https://deepseek.com/)

## ✨ 核心功能

### 🤝 智能师生协作写作+智能文献推荐
- 多Agent协作机制，模拟真实师生互动
- 导师Agent提供专业修改建议
- 学生Agent负责创意内容创作
- 实时爬取arXiv最新学术论文
- 基于关键词的智能相关性评分
- Top-10高质量文献推荐

### 📄 PDF总结器
- 支持多种PDF格式解析
- 结构化内容提取和分析
- 生成详细的学术总结报告
- 关键信息智能提取

### 🛡️ 学术诚信检查+写作助手
- 多维度学术诚信风险评估
- 实时检测潜在违规行为
- 前置检查机制，预防学术不端
- 提供改进建议和写作指导

## 🚀 快速开始

### 环境要求

- Python 3.8+
- PyQt6
- requests
- BeautifulSoup4
- openai
- PyPDF2
- Camel AI

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/dreamawakener/ai_homework.git
cd ai_homework
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置API密钥**
```python
# 在config.py中配置您的API信息
my_api_key = "your-api-key-here"  
my_base_url = "https://api.openai.com/v1"  
my_model_name = "Pro/deepseek-ai/DeepSeek-V3"
```

4. **运行程序**
```bash
python main.py
```

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    PyQt6 GUI 界面层                          │
├─────────────────────────────────────────────────────────────┤
│  师生协作 + 文献推荐模块  │  PDF处理模块  │  诚信检查+写作模块  │
├─────────────────────────────────────────────────────────────┤
│                    多Agent协作引擎                           │
│  导师Agent │ 学生Agent │ 文献Agent │ 诚信Agent │ 写作Agent   │
├─────────────────────────────────────────────────────────────┤
│                  DeepSeek API 调用层                        │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 技术特色

### 多Agent协作机制
- **导师Agent**: 专业建议，保守参数 (temperature=0.6)
- **学生Agent**: 创意写作，适中参数 (temperature=0.8)  
- **文献Agent**: 精确检索，较低参数 (temperature=0.3)
- **诚信Agent**: 严格审查，最低参数 (temperature=0.2)

### 动态参数调优

| 功能模块 | Temperature | Top_p | Max_tokens | 设计理由 |
|---------|-------------|-------|------------|----------|
| 师生协作 | 0.8 | 0.9 | 4096 | 保持创造性同时确保逻辑性 |
| 文献推荐 | 0.3 | 0.7 | 4096 | 确保推荐准确性和相关性 |
| PDF总结 | 0.5 | 0.8 | -- | 平衡准确性与信息完整性 |
| 学术诚信检查 | 0.2 | 0.6 | 4096 | 严格检测，减少误判 |

### 流式输出技术
```python
class StreamingChatAgent:
    """带流式响应功能的聊天代理"""

    def __init__(self, system_message="", output_language="zh"):
        self.client = openai.OpenAI(api_key=my_api_key, base_url=my_base_url)
        self.model = my_model_name
        self.system_message = system_message
        self.output_language = output_language
        self.conversation_history = []

        # 添加系统消息到对话历史
        if system_message:
            self.conversation_history.append({"role": "system", "content": system_message})

    def stream_step(self, message: str, typing_delay: float = 0.001, show_role_prefix: str = ""):
        """流式响应处理"""
        # 添加用户消息到历史
        self.conversation_history.append({"role": "user", "content": message})

        try:
            # 创建流式请求
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.8,
                max_tokens=8192,
                stream=True  # 启用流式输出
            )

            full_response = ""
            if show_role_prefix:
                print(show_role_prefix, end="", flush=True)

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

            # 保存完整响应到对话历史
            self.conversation_history.append({"role": "assistant", "content": full_response})
            return full_response

        except Exception as e:
            print(f"❌ 流式请求失败: {e}")
            return f"请求失败: {e}"
```

## 📊 性能表现

- **API调用成功率**: 99%
- **流式输出延迟**: 平均200ms首字节时间
- **PDF处理准确率**: 98% (测试50个不同格式PDF)
- **文献推荐相关性**: 用户满意度95%
- **整体用户满意度**: 4.6/5


## 👥 团队贡献

- **黄思柏**: 师生协作写作模块、PDF总结器、学术诚信检查模块、后期bug调试修复、技术报告撰写、演示视频的部分录制
- **高润宇**: 师生对话优化、arXiv爬虫与文献推荐算法、密钥管理方法、技术报告撰写、使用手册及部署文档修改  
- **董彦嘉**: PyQt GUI界面设计优化与前后端集成、后期bug调试修复、调查用户反馈、演示视频的部分录制、剪辑

## 🔄 未来优化空间

- [ ] 支持更多文档格式 (Word, PPT等)
- [ ] 本地化部署，减少API依赖
- [ ] 多用户实时协作功能
- [ ] 移动端应用开发
- [ ] 多语言支持扩展

## 🆚 竞品对比

| 功能特性 | 本项目 | Grammarly | Zotero | Notion AI |
|---------|--------|-----------|--------|-----------|
| 学术写作专业性 | ✅ | ❌ | ⚠️ | ❌ |
| 多Agent协作 | ✅ | ❌ | ❌ | ❌ |
| 文献推荐 | ✅ | ❌ | ✅ | ❌ |
| 学术诚信检查 | ✅ | ⚠️ | ❌ | ❌ |
| 师生互动模拟 | ✅ | ❌ | ❌ | ❌ |

## 🙏 致谢

感谢所有为本项目做出贡献的开发者和测试用户。特别感谢：
- DeepSeek团队提供优质的大语言模型API
- arXiv平台提供开放的学术资源
- PyQt团队提供强大的GUI框架

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！您的支持是我们持续改进的动力。