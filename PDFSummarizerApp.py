#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于流式API的PDF文件总结器
支持本地PDF文件选择、智能总结和真实流式输出
"""

import os
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import PyPDF2
import threading
from openai import OpenAI

# API配置
my_api_key = "sk-qullgfjnwatfbztwedpwajnagikznfbimlotgxhlloyrbkax"
my_base_url = "https://api.siliconflow.cn/v1"
my_model_name = "Pro/deepseek-ai/DeepSeek-V3"

class StreamingChatAgent:
    """流式聊天代理"""
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.conversation_history = [
            {
                "role": "system",
                "content": """你是一个专业的论文总结专家。你的任务是阅读PDF论文文档内容，
提取关键信息，并生成简洁明了的中文总结。请确保总结包含：
1. 📋 文档主要主题和目的
2. 💡 核心观点、论据和发现
3. 📊 重要结论和建议
4. 📈 关键数据、统计信息或事实
5. 🔬 研究方法和过程
6. 💼 文档的价值和意义

请以结构化的方式逐步展示总结内容，使用清晰的标题和分段。"""
            }
        ]
        
        # 流式输出控制
        self.streaming_callback = None
        self.stop_streaming = False
    
    def set_streaming_callback(self, callback):
        """设置流式输出回调函数"""
        self.streaming_callback = callback
    
    def stream_step(self, message: str, typing_delay: float = 0.01):
        """流式响应处理 - GUI版本"""
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
            
            # 逐块处理流式响应
            for chunk in stream:
                # 检查是否需要停止
                if self.stop_streaming:
                    break
                    
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # 通过回调函数更新GUI
                    if self.streaming_callback:
                        self.streaming_callback(content)
                    
                    # 控制输出速度
                    time.sleep(typing_delay)
            
            # 保存完整响应到对话历史
            if not self.stop_streaming:
                self.conversation_history.append({"role": "assistant", "content": full_response})
            
            return full_response
            
        except Exception as e:
            error_msg = f"❌ 流式请求失败: {e}"
            if self.streaming_callback:
                self.streaming_callback(f"\n\n{error_msg}")
            return error_msg
    
    def stop_stream(self):
        """停止流式输出"""
        self.stop_streaming = True
    
    def reset_stream(self):
        """重置流式状态"""
        self.stop_streaming = False

class PDFSummarizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF智能总结器 - 真实流式输出版")
        self.root.geometry("950x800")
        self.root.configure(bg='#f0f0f0')
        
        # 初始化流式AI代理
        self.setup_streaming_agent()
        
        # 创建界面
        self.create_widgets()
        
        # 存储PDF内容和状态
        self.pdf_content = ""
        self.is_streaming = False
        self.current_summary = ""
        self.total_chars_streamed = 0
        
    def setup_streaming_agent(self):
        """设置流式AI代理"""
        try:
            if not my_api_key or not my_base_url or not my_model_name:
                raise ValueError("请设置正确的API配置")
            
            self.agent = StreamingChatAgent(
                api_key=my_api_key,
                base_url=my_base_url,
                model=my_model_name
            )
            
            # 设置流式输出回调
            self.agent.set_streaming_callback(self.on_streaming_content)
            
        except Exception as e:
            messagebox.showerror("错误", f"初始化流式AI代理失败: {str(e)}")
            self.agent = None
    
    def on_streaming_content(self, content: str):
        """处理流式内容回调"""
        def update_gui():
            try:
                # 更新文本显示区域
                self.result_text.config(state='normal')
                self.result_text.insert(tk.END, content)
                self.result_text.see(tk.END)
                self.result_text.config(state='disabled')
                
                # 更新当前总结内容
                self.current_summary += content
                self.total_chars_streamed += len(content)
                
                # 更新字数统计
                word_count = len(self.current_summary.replace(' ', '').replace('\n', ''))
                self.word_count_label.config(text=f"字数: {word_count}")
                
                # 更新实时状态
                self.realtime_status.config(text=f"已生成 {self.total_chars_streamed} 字符")
                
            except Exception as e:
                print(f"GUI更新错误: {e}")
        
        # 在主线程中更新GUI
        self.root.after(0, update_gui)
    
    def create_widgets(self):
        """创建界面组件"""
        # 主标题
        title_label = tk.Label(
            self.root,
            text="🤖 PDF智能总结器 - 真实流式输出版",
            font=("微软雅黑", 16, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # API状态指示
        self.api_status_label = tk.Label(
            self.root,
            text="🟢 API连接正常" if self.agent else "🔴 API连接失败",
            font=("微软雅黑", 9),
            bg='#f0f0f0',
            fg='#27ae60' if self.agent else '#e74c3c'
        )
        self.api_status_label.pack()
        
        # 文件选择框架
        file_frame = tk.Frame(self.root, bg='#f0f0f0')
        file_frame.pack(pady=15, padx=20, fill='x')
        
        self.file_label = tk.Label(
            file_frame,
            text="📄 未选择文件",
            font=("微软雅黑", 10),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        self.file_label.pack(side='left')
        
        select_btn = tk.Button(
            file_frame,
            text="📁 选择PDF文件",
            command=self.select_file,
            font=("微软雅黑", 10),
            bg='#3498db',
            fg='white',
            relief='flat',
            padx=20
        )
        select_btn.pack(side='right')
        
        # 控制按钮框架
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(pady=20)
        
        # 开始总结按钮
        self.summarize_btn = tk.Button(
            control_frame,
            text="🚀 开始流式总结",
            command=self.start_summarization,
            font=("微软雅黑", 12, "bold"),
            bg='#27ae60',
            fg='white',
            relief='flat',
            padx=30,
            pady=10,
            state='disabled'
        )
        self.summarize_btn.pack(side='left', padx=10)
        
        # 停止按钮
        self.stop_btn = tk.Button(
            control_frame,
            text="⏹️ 停止生成",
            command=self.stop_summarization,
            font=("微软雅黑", 12, "bold"),
            bg='#e74c3c',
            fg='white',
            relief='flat',
            padx=30,
            pady=10,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=10)
        
        # 清空按钮
        self.clear_btn = tk.Button(
            control_frame,
            text="🗑️ 清空结果",
            command=self.clear_result,
            font=("微软雅黑", 10),
            bg='#95a5a6',
            fg='white',
            relief='flat',
            padx=20,
            pady=5
        )
        self.clear_btn.pack(side='left', padx=10)
        
        # 速度控制框架
        speed_frame = tk.Frame(self.root, bg='#f0f0f0')
        speed_frame.pack(pady=10)
        
        tk.Label(
            speed_frame,
            text="⚡ 输出速度:",
            font=("微软雅黑", 9),
            bg='#f0f0f0'
        ).pack(side='left')
        
        self.speed_var = tk.DoubleVar(value=0.01)
        self.speed_scale = tk.Scale(
            speed_frame,
            from_=0.001,
            to=0.1,
            resolution=0.001,
            orient='horizontal',
            variable=self.speed_var,
            length=200,
            bg='#f0f0f0'
        )
        self.speed_scale.pack(side='left', padx=10)
        
        tk.Label(
            speed_frame,
            text="(慢 ← → 快)",
            font=("微软雅黑", 8),
            bg='#f0f0f0',
            fg='#7f8c8d'
        ).pack(side='left')
        
        # 状态和进度框架
        status_frame = tk.Frame(self.root, bg='#f0f0f0')
        status_frame.pack(pady=10, fill='x', padx=20)
        
        # 进度条
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=400
        )
        self.progress.pack(side='left', fill='x', expand=True)
        
        # 实时状态标签
        self.realtime_status = tk.Label(
            status_frame,
            text="",
            font=("微软雅黑", 9),
            bg='#f0f0f0',
            fg='#e67e22',
            width=25
        )
        self.realtime_status.pack(side='right', padx=10)
        
        # 状态标签
        self.status_label = tk.Label(
            self.root,
            text="📋 请选择PDF文件开始智能总结",
            font=("微软雅黑", 10),
            bg='#f0f0f0',
            fg='#95a5a6'
        )
        self.status_label.pack()
        
        # 结果显示区域
        result_frame = tk.Frame(self.root, bg='#f0f0f0')
        result_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        result_header = tk.Frame(result_frame, bg='#f0f0f0')
        result_header.pack(fill='x')
        
        result_label = tk.Label(
            result_header,
            text="📝 总结结果（AI实时流式生成）：",
            font=("微软雅黑", 12, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        result_label.pack(side='left')
        
        # 字数统计标签
        self.word_count_label = tk.Label(
            result_header,
            text="字数: 0",
            font=("微软雅黑", 9),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        self.word_count_label.pack(side='right')
        
        # 文本显示区域
        text_frame = tk.Frame(result_frame)
        text_frame.pack(fill='both', expand=True, pady=10)
        
        self.result_text = scrolledtext.ScrolledText(
            text_frame,
            wrap='word',
            width=85,
            height=25,
            font=("微软雅黑", 10),
            bg='white',
            fg='#2c3e50',
            relief='solid',
            borderwidth=1,
            state='disabled'
        )
        self.result_text.pack(fill='both', expand=True)
        
        # 底部按钮框架
        bottom_frame = tk.Frame(self.root, bg='#f0f0f0')
        bottom_frame.pack(pady=15, fill='x', padx=20)
        
        # 保存按钮
        self.save_btn = tk.Button(
            bottom_frame,
            text="💾 保存总结",
            command=self.save_summary,
            font=("微软雅黑", 10),
            bg='#9b59b6',
            fg='white',
            relief='flat',
            padx=20,
            state='disabled'
        )
        self.save_btn.pack(side='left')
        
        # 复制按钮
        self.copy_btn = tk.Button(
            bottom_frame,
            text="📋 复制到剪贴板",
            command=self.copy_to_clipboard,
            font=("微软雅黑", 10),
            bg='#34495e',
            fg='white',
            relief='flat',
            padx=20,
            state='disabled'
        )
        self.copy_btn.pack(side='left', padx=10)
        
        # 重新生成按钮
        self.regenerate_btn = tk.Button(
            bottom_frame,
            text="🔄 重新生成",
            command=self.regenerate_summary,
            font=("微软雅黑", 10),
            bg='#f39c12',
            fg='white',
            relief='flat',
            padx=20,
            state='disabled'
        )
        self.regenerate_btn.pack(side='left', padx=10)
    
    def select_file(self):
        """选择PDF文件"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        if file_path:
            self.file_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"📄 已选择: {filename}")
            if self.agent:
                self.summarize_btn.config(state='normal')
            self.status_label.config(text="✅ 文件已选择，点击开始流式总结")
    
    def extract_pdf_text(self):
        """提取PDF文本内容"""
        try:
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                total_pages = len(pdf_reader.pages)
                for page_num in range(total_pages):
                    # 更新实时状态
                    self.root.after(0, lambda p=page_num+1, t=total_pages: 
                                  self.realtime_status.config(text=f"📖 读取 {p}/{t} 页"))
                    
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                    
                    # 让界面有机会更新
                    time.sleep(0.1)
                
                return text.strip()
                
        except Exception as e:
            raise Exception(f"PDF读取失败: {str(e)}")
    
    def start_summarization(self):
        """开始流式总结"""
        if not self.agent:
            messagebox.showerror("错误", "AI代理未初始化，请检查API配置")
            return
            
        def summarize_task():
            try:
                # 重置状态
                self.is_streaming = True
                self.total_chars_streamed = 0
                self.current_summary = ""
                self.agent.reset_stream()
                
                # 更新界面状态
                self.root.after(0, lambda: self.update_ui_for_start())
                
                # 提取PDF文本
                pdf_text = self.extract_pdf_text()
                
                if not pdf_text.strip():
                    raise Exception("PDF文件为空或无法提取文本内容")
                
                # 准备总结提示词
                prompt = f"""
请对以下PDF文档内容进行详细的中文总结分析：

{pdf_text}

请按照以下结构提供总结：
1. 📋 **文档概述**: 简要说明文档的主要主题、类型和目的
2. 💡 **核心观点**: 列出文档中的主要观点、论据和重要发现
3. 📊 **关键结论**: 总结文档得出的重要结论和建议
4. 📈 **数据要点**: 提取重要的数据、统计信息或关键事实
5. 🔬 **方法论**: 如果适用，说明文档使用的研究方法或分析过程
6. 💼 **价值意义**: 分析文档的价值、意义和可能的应用场景

请确保总结内容结构清晰、重点突出、易于理解。
"""
                
                # 开始流式总结
                self.root.after(0, lambda: self.update_status("🤖 AI正在进行流式总结..."))
                self.root.after(0, lambda: self.realtime_status.config(text="AI思考中..."))
                
                # 执行流式总结
                summary = self.agent.stream_step(prompt, typing_delay=self.speed_var.get())
                
                # 完成处理
                if not self.agent.stop_streaming:
                    self.root.after(0, lambda: self.on_summarization_complete())
                else:
                    self.root.after(0, lambda: self.on_summarization_stopped())
                    
            except Exception as e:
                self.root.after(0, lambda: self.handle_error(str(e)))
            finally:
                self.is_streaming = False
        
        # 在后台线程中执行
        thread = threading.Thread(target=summarize_task)
        thread.daemon = True
        thread.start()
    
    def update_ui_for_start(self):
        """更新开始时的UI状态"""
        self.update_status("📖 正在读取PDF文件...")
        self.progress.start()
        self.summarize_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.regenerate_btn.config(state='disabled')
        self.realtime_status.config(text="准备中...")
        
        # 清空之前的结果
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state='disabled')
        self.word_count_label.config(text="字数: 0")
    
    def on_summarization_complete(self):
        """总结完成时的处理"""
        self.update_status("✅ 流式总结完成！")
        self.realtime_status.config(text="✨ 已完成")
        self.progress.stop()
        self.summarize_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.save_btn.config(state='normal')
        self.copy_btn.config(state='normal')
        self.regenerate_btn.config(state='normal')
    
    def on_summarization_stopped(self):
        """总结被停止时的处理"""
        self.update_status("⏹️ 流式总结已停止")
        self.realtime_status.config(text="已停止")
        self.progress.stop()
        self.summarize_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        if self.current_summary.strip():
            self.save_btn.config(state='normal')
            self.copy_btn.config(state='normal')
        self.regenerate_btn.config(state='normal')
    
    def stop_summarization(self):
        """停止流式总结"""
        if self.agent:
            self.agent.stop_stream()
        self.stop_btn.config(state='disabled')
        self.update_status("⏹️ 正在停止...")
        self.realtime_status.config(text="停止中...")
    
    def regenerate_summary(self):
        """重新生成总结"""
        if self.is_streaming:
            messagebox.showwarning("警告", "请先停止当前的生成过程")
            return
        
        if not hasattr(self, 'file_path'):
            messagebox.showwarning("警告", "请先选择PDF文件")
            return
            
        # 重新开始总结
        self.start_summarization()
    
    def clear_result(self):
        """清空结果"""
        if self.is_streaming:
            messagebox.showwarning("警告", "请先停止当前的总结过程")
            return
            
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state='disabled')
        self.current_summary = ""
        self.total_chars_streamed = 0
        self.word_count_label.config(text="字数: 0")
        self.save_btn.config(state='disabled')
        self.copy_btn.config(state='disabled')
        self.update_status("🗑️ 结果已清空")
        self.realtime_status.config(text="")
    
    def update_status(self, message):
        """更新状态信息"""
        self.status_label.config(text=message)
    
    def handle_error(self, error_message):
        """处理错误"""
        self.progress.stop()
        self.summarize_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.regenerate_btn.config(state='normal')
        self.status_label.config(text="❌ 总结失败")
        self.realtime_status.config(text="出错了")
        self.is_streaming = False
        messagebox.showerror("错误", error_message)
    
    def copy_to_clipboard(self):
        """复制到剪贴板"""
        if not self.current_summary.strip():
            messagebox.showwarning("警告", "没有可复制的内容")
            return
        
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_summary)
            messagebox.showinfo("成功", "📋 总结内容已复制到剪贴板！")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {str(e)}")
    
    def save_summary(self):
        """保存总结结果"""
        if not self.current_summary.strip():
            messagebox.showwarning("警告", "没有可保存的总结内容")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存总结",
            defaultextension=".md",
            filetypes=[
                ("Markdown文件", "*.md"),
                ("文本文件", "*.txt"), 
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(f"# 📄 PDF文档智能总结报告\n\n")
                    file.write(f"---\n\n")
                    file.write(f"**📁 原文件**: {os.path.basename(self.file_path)}\n\n")
                    file.write(f"**⏰ 总结时间**: {self.get_current_time()}\n\n")
                    word_count = len(self.current_summary.replace(' ', '').replace('\n', ''))
                    file.write(f"📊 总结字数: {word_count}\n\n")
                    file.write(f"**🤖 生成方式**: AI流式实时生成\n\n")
                    file.write(f"---\n\n")
                    file.write(f"## 📋 总结内容\n\n")
                    file.write(self.current_summary)
                    file.write(f"\n\n---\n\n")
                    file.write(f"*本总结由AI流式生成，生成时间: {self.get_current_time()}*\n")
                
                messagebox.showinfo("成功", f"✅ 总结已保存到:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def get_current_time(self):
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """主函数"""
    # 检查API配置
    if not my_api_key or not my_base_url or not my_model_name:
        print("⚠️  请设置正确的API配置")
        print("请在代码顶部修改以下变量:")
        print("- my_api_key: 你的API密钥")
        print("- my_base_url: API基础URL")  
        print("- my_model_name: 模型名称")
        
        # 仍然启动程序，但会显示错误状态
        
    root = tk.Tk()
    app = PDFSummarizerApp(root)
    
    try:
        print("🚀 PDF智能总结器启动成功!")
        print("✨ 核心功能:")
        print("   - 真实API流式输出")
        print("   - 可调节输出速度")
        print("   - 随时停止/重新生成")
        print("   - 实时字数统计")
        print("   - 一键复制和保存")
        print("   - Markdown格式导出")
        root.mainloop()
    except KeyboardInterrupt:
        print("\n❌ 程序被用户中断")
    except Exception as e:
        print(f"💥 程序运行出错: {e}")


if __name__ == "__main__":
    main()