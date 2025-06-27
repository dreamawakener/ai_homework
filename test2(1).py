import openai
import sys
import time
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
import re
from datetime import datetime, timedelta
from typing import List, Dict
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType
from camel.utils import print_text_animated
from colorama import Fore, init
from camel.societies import RolePlaying
from dotenv import load_dotenv
import os
import json
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote
# 初始化colorama
init(autoreset=True)


# 导入配置管理
from config import get_api_key, get_base_url, get_model_name

my_api_key = get_api_key()
my_base_url = get_base_url()
my_model_name = get_model_name()


class ArxivCrawler:
    """ArXiv论文爬虫 - 使用网页搜索"""

    def __init__(self):
        self.base_url = "https://arxiv.org/search/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.openai_client = openai.OpenAI(api_key=my_api_key, base_url=my_base_url)
        self.model_name = my_model_name
    def translate_query(self, query: str) -> str:
        """将中文查询词翻译为英文"""
        try:
            # 检查是否包含中文字符
            if any('\u4e00' <= char <= '\u9fff' for char in query):
                print(Fore.YELLOW + f"🔍 检测到中文查询词: {query}，正在翻译...")
                # 构建翻译提示
                prompt = f"请将以下中文查询词翻译为英文，用于学术文献搜索：\n{query}"
                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "你是一名专业的学术翻译专家，需将中文准确译为英文学术关键词"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=100
                )
                # 提取翻译结果（去除可能的标点和多余空格）
                translation = response.choices[0].message.content.strip()
                # 处理可能的标点符号（如结尾的句号）
                if translation.endswith('.'):
                    translation = translation[:-1]
                print(Fore.GREEN + f"✅ 翻译完成: {translation}")
                return translation
            return query  # 非中文直接返回原词
        except Exception as e:
            print(Fore.RED + f"❌ 翻译失败: {e}，使用原词搜索")
            return query
    def search_papers(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        从ArXiv搜索相关论文
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
        Returns:
            论文信息列表
        """
        translated_query = self.translate_query(query)
        print(Fore.YELLOW + f"🔍 正在ArXiv搜索: {translated_query}")

        papers = []
        page = 0
        per_page = 50  # ArXiv每页最多显示50篇论文

        try:
            while len(papers) < max_results:
                # 构建搜索URL
                params = {
                    'query': translated_query,
                    'searchtype': 'all',
                    'source': 'header',
                    'start': page * per_page
                }

                print(Fore.CYAN + f"🌐 正在获取第 {page + 1} 页...")

                response = requests.get(self.base_url, params=params, headers=self.headers, timeout=30)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # 查找论文条目
                paper_items = soup.find_all('li', class_='arxiv-result')

                if not paper_items:
                    print(Fore.YELLOW + f"⚠️  第 {page + 1} 页没有找到论文，停止搜索")
                    break

                print(Fore.GREEN + f"✅ 第 {page + 1} 页找到 {len(paper_items)} 篇论文")

                # 解析每篇论文
                for item in paper_items:
                    if len(papers) >= max_results:
                        break

                    paper_info = self._parse_paper_item(item)
                    if paper_info:
                        papers.append(paper_info)

                # 检查是否还有更多页面
                if len(paper_items) < per_page:
                    break

                page += 1
                time.sleep(1)  # 避免请求过快

        except requests.RequestException as e:
            print(Fore.RED + f"❌ 网络请求失败: {e}")
        except Exception as e:
            print(Fore.RED + f"❌ 解析失败: {e}")

        print(Fore.GREEN + f"✅ 总共找到 {len(papers)} 篇相关论文")
        return papers

    def _parse_paper_item(self, item) -> Dict:
        """解析单个论文条目"""
        try:
            # 获取标题
            title = item.find('p', class_="title is-5 mathjax").text
            if title:
                # print(title)
                pass
            else:
                title = "未知标题"
                print("获取标题失败")

            # 获取摘要链接
            abs_link = item.find('p', class_='list-title is-inline-block').find('a')['href']
            if abs_link:
                # print(abs_link)
                pass
            else:
                abs_link = "#"
                print("获取abs_link失败")

            # 获取ArXiv ID
            arxiv_id = item.find('p', class_='list-title is-inline-block').find('a').text.split(':')[1]
            if arxiv_id:
                # print(arxiv_id)
                pass
            else:
                arxiv_id = "未知ID"
                print("获取arxiv_id失败")

            # 构建PDF链接
            pdf_link = f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else "#"

            # 获取作者
            authors = []
            authors_elem = item.find('p', class_='authors')
            if authors_elem:
                author_links = authors_elem.find_all('a')
                for author_link in author_links:
                    authors.append(author_link.text.strip())

            # 获取摘要
            abstract_elem = item.find('p', class_='abstract')
            if abstract_elem:
                abstract_text = abstract_elem.text.strip()
                if abstract_text.startswith('Abstract:'):
                    summary = abstract_text[9:].strip()
            else:
                summary = "无摘要"

            # 获取发布日期
            submitted_elem = item.find('p', class_='is-size-7')
            published_date = submitted_elem.text.strip() if submitted_elem else "未知日期"

            # 获取分类信息
            categories = []
            subject_elem = item.find('div', class_='tags is-inline-block')
            if subject_elem:
                tag_links = subject_elem.find_all(class_='tag')
                for tag_link in tag_links:
                    category = tag_link.text.strip()
                    if category:
                        categories.append(category)

            # 限制摘要长度
            if len(summary) > 500:
                summary = summary[:500] + '...'

            return {
                'title': title,
                'authors': authors,
                'summary': summary,
                'published_date': published_date,
                'arxiv_id': arxiv_id,
                'pdf_link': pdf_link,
                'abs_link': abs_link,
                'categories': categories,
                'authors_str': ', '.join(authors[:3]) + (' et al.' if len(authors) > 3 else '')
            }

        except Exception as e:
            print(Fore.RED + f"❌ 解析论文条目失败: {e}")
            return None

class PaperValueAssessmentAgent:
    """论文价值评估代理"""

    def __init__(self):
        self.client = openai.OpenAI(api_key=my_api_key, base_url=my_base_url)
        self.model = my_model_name

    def assess_papers(self, papers: List[Dict], theme: str, subject: str, outline: str) -> List[Dict]:
        """
        评估论文价值并排序

        Args:
            papers: 论文列表
            theme: 论文主题方向
            subject: 具体主题
            outline: 论文提纲

        Returns:
            按价值排序的论文列表
        """
        print(Fore.YELLOW + f"🎯 正在评估 {len(papers)} 篇论文的参考价值...")

        # 构建评估提示
        assessment_prompt = self._build_assessment_prompt(papers, theme, subject, outline)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",
                    "content": "你是一名学术评估专家，需要根据论文与给定主题的相关性、引用价值、研究质量等因素对论文进行评分排序。"},
                    {"role": "user", "content": assessment_prompt}
                ],
                temperature=0.3,
                max_tokens=4096
            )

            assessment_result = response.choices[0].message.content
            ranked_papers = self._parse_assessment_result(assessment_result, papers)

            print(Fore.GREEN + f"✅ 论文价值评估完成，推荐前 {min(10, len(ranked_papers))} 篇")
            return ranked_papers[:10]  # 返回前10篇

        except Exception as e:
            print(Fore.RED + f"❌ 论文评估失败: {e}")
            # 如果评估失败，按发布时间排序返回
            return sorted(papers, key=lambda x: x['published_date'], reverse=True)[:10]

    def _build_assessment_prompt(self, papers: List[Dict], theme: str, subject: str, outline: str) -> str:
        """构建评估提示"""
        papers_info = ""
        for i, paper in enumerate(papers, 1):
            papers_info += f"""
论文{i}:
- 标题: {paper['title']}
- 作者: {paper['authors_str']}
- 摘要: {paper['summary']}
- 发布时间: {paper['published_date']}
- 分类: {', '.join(paper['categories'][:3])}
---
"""

        prompt = f"""
请评估以下论文对于"{theme}"领域中"{subject}"主题研究的参考价值。

研究提纲:
{outline}

待评估论文:
{papers_info}

评估标准:
1. 与研究主题的相关性 (40%)
2. 研究方法的创新性和严谨性 (25%)
3. 发表时间的新颖性 (20%)
4. 作者权威性和期刊质量 (15%)

请按以下JSON格式输出评估结果，包含每篇论文的评分(1-10分)和排序:
```json
{{
  "rankings": [
    {{
      "paper_index": 1,
      "score": 8.5,
      "reasoning": "相关性高，方法创新..."
    }},
    ...
  ]
}}
```

请确保JSON格式正确，按评分从高到低排序。
"""
        return prompt

    def _parse_assessment_result(self, assessment_result: str, papers: List[Dict]) -> List[Dict]:
        """解析评估结果"""
        try:
            # 提取JSON部分
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', assessment_result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                assessment_data = json.loads(json_str)

                # 按评估结果排序论文
                ranked_papers = []
                for ranking in assessment_data.get('rankings', []):
                    paper_index = ranking.get('paper_index', 1) - 1  # 转换为0基索引
                    if 0 <= paper_index < len(papers):
                        paper = papers[paper_index].copy()
                        paper['assessment_score'] = ranking.get('score', 0)
                        paper['assessment_reasoning'] = ranking.get('reasoning', '')
                        ranked_papers.append(paper)

                return ranked_papers

        except (json.JSONDecodeError, KeyError) as e:
            print(Fore.YELLOW + f"⚠️  评估结果解析失败，使用默认排序: {e}")

        # 如果解析失败，按发布时间排序
        return sorted(papers, key=lambda x: x['published_date'], reverse=True)

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


class StreamingPaperWritingSystem:
    """带流式响应的论文写作系统"""

    def __init__(self):
        self.camel_model = ModelFactory.create(
            model_platform = ModelPlatformType.OPENAI,
            model_type=my_model_name,
            url=my_base_url,
            api_key=my_api_key,
            model_config_dict={
                "max_tokens": 4096
            }
        )

        # 初始化变量
        self.theme = ""
        self.subject = ""
        self.outline = ""
        self.arxiv_crawler = ArxivCrawler()
        self.value_assessor = PaperValueAssessmentAgent()

    def generate_outline(self):
        self.theme = input("请输入论文主要方向（如：医学、数学、语文等）：")
        self.subject = input("请输入论文主题（如：心血管疾病、微积分、古代诗词等）：")

        # 创建提纲生成Agent
        outline_agent = StreamingChatAgent(
            system_message="你是一名学术写作专家，需生成包含以下要素的论文提纲：\n"
                           "1. 严格遵循IMRaD结构（引言、方法、结果、讨论）\n"
                           "2. 每个章节至少包含2个子章节\n"
                           "3. 用Markdown格式输出层级标题",
            output_language="zh"
        )
        print(Fore.YELLOW + "\n🔄 正在生成提纲...")

        self.outline = outline_agent.stream_step(
            f"请生成关于{self.theme}的有关{self.subject}内容的论文提纲",
            typing_delay=0.01,
            show_role_prefix=""
        )

    def start_collaborative_writing(self, rounds=3):
        """开始协作写作过程"""
        print(Fore.MAGENTA + f"\n🎯 开始师生协作优化（共{rounds}轮）")
        print("=" * 60)

        # 创建流式代理
        assistant_agent = StreamingChatAgent(
            system_message=f"""你是一名要求严格的导师(RoleType:ASSISTANT)，必须按以下规则指导：
                            1. 用'逻辑问题X：...'格式指出提纲缺陷
                            2. 每次只提1个核心问题
                            3. 避免直接给出答案
                            4. 重点关注{self.theme}领域的{self.subject}专业问题""",
            output_language="zh"
        )

        user_agent = StreamingChatAgent(
            system_message=f"""你是学生（RoleType.USER），你正在撰写关于{self.theme}的有关{self.subject}内容的论文，你的任务是：
                            1. 根据导师的意见对提纲作出修改
                            2. 最终生成修订版提纲""",
            output_language="zh"
        )

        # 学生发送初始消息
        user_msg = f"以下是我的论文提纲，请批评指正：\n\n{self.outline}"

        for i in range(rounds):
            # 导师流式回复
            print(Fore.BLUE + f"\n👨‍🏫 导师 第{i + 1}轮:")
            assistant_msg = assistant_agent.stream_step(
                user_msg,
                typing_delay=0.001,
                show_role_prefix=""
            )

            # 最后一轮指导后直接生成最终提纲
            if i + 1 == rounds:
                assistant_msg = assistant_msg + "注意！这一版修改完毕后请*直接*输出完整的可以直接拷贝的md格式提纲！否则不予通过！"

            # 学生流式回复
            print(Fore.GREEN + f"\n🧑‍🎓 学生 第{i + 1}轮回应:")
            user_msg = user_agent.stream_step(
                assistant_msg,
                typing_delay=0.001,
                show_role_prefix=""
            )

        print(Fore.CYAN + "\n🎉 协作优化完成！")
        return user_msg

    def save_final_outline(self, final_outline):
        """保存最终提纲"""
        filename = f"{self.theme}_{self.subject}_论文提纲.md"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {self.theme} - {self.subject} 论文提纲\n\n")
                f.write(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## 最终优化提纲\n\n")
                f.write(final_outline)

            print(Fore.GREEN + f"\n💾 最终提纲已保存至: {filename}")
        except Exception as e:
            print(Fore.RED + f"\n❌ 保存失败: {e}")

    def search_and_save_references(self, final_outline):
        """使用ArXiv爬虫搜索并评估参考文献"""
        print(Fore.YELLOW + "\n🔍 正在从ArXiv搜索相关论文...")

        # 构建搜索关键词
        search_query = f"{self.subject} {self.theme}"

        # 爬取论文
        papers = self.arxiv_crawler.search_papers(search_query, max_results=50)

        if not papers:
            print(Fore.RED + "❌ 未找到相关论文")
            return

        # 评估论文价值
        ranked_papers = self.value_assessor.assess_papers(papers, self.theme, self.subject, final_outline)

        # 保存参考文献
        filename = f"{self.theme}_{self.subject}_参考文献.md"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {self.theme} - {self.subject} 参考文献\n\n")
                f.write(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**搜索关键词**: {search_query}\n")
                f.write(f"**总共找到**: {len(papers)} 篇论文\n")
                f.write(f"**推荐**: 前 {len(ranked_papers)} 篇高价值论文\n\n")

                f.write("## 推荐文献列表\n\n")

                for i, paper in enumerate(ranked_papers, 1):
                    f.write(f"### {i}. {paper['title']}\n\n")
                    f.write(f"**作者**: {paper['authors_str']}\n\n")
                    f.write(f"**发布时间**: {paper['published_date']}\n\n")
                    f.write(f"**ArXiv ID**: {paper['arxiv_id']}\n\n")
                    f.write(f"**分类**: {', '.join(paper['categories'][:3])}\n\n")
                    f.write(f"**链接**: \n")
                    f.write(f"- [论文摘要]({paper['abs_link']})\n")
                    f.write(f"- [PDF下载]({paper['pdf_link']})\n\n")
                    f.write(f"**摘要**: {paper['summary']}\n\n")

                    if 'assessment_score' in paper:
                        f.write(f"**评估分数**: {paper['assessment_score']}/10\n\n")
                    if 'assessment_reasoning' in paper:
                        f.write(f"**推荐理由**: {paper['assessment_reasoning']}\n\n")

                    f.write("---\n\n")

            print(Fore.GREEN + f"\n💾 参考文献已保存至: {filename}")
            print(Fore.CYAN + f"📊 共推荐 {len(ranked_papers)} 篇高质量论文")

        except Exception as e:
            print(Fore.RED + f"\n❌ 保存失败: {e}")

    def run(self):
        try:
            # 1. 生成提纲
            self.generate_outline()
            # 2. 开始协作优化
            final_outline = self.start_collaborative_writing(rounds=1)
            # 3. 保存最终提纲
            self.save_final_outline(final_outline)
            # 4. 使用ArXiv爬虫查找并评估参考文献
            self.search_and_save_references(final_outline)

        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\n⚠️  用户中断程序")
        except Exception as e:
            print(Fore.RED + f"\n❌ 系统错误: {e}")


# 运行系统
if __name__ == "__main__":
    system = StreamingPaperWritingSystem()
    system.run()