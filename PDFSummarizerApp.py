#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于流式API的PDF文件总结器 - PyQt6版本
支持本地PDF文件选择、智能总结和真实流式输出
"""

import os
import sys
import time
from datetime import datetime
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                            QFileDialog, QMessageBox, QProgressBar, QSlider,
                            QFrame, QSplitter, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QTextCursor, QClipboard
import PyPDF2
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
                stream=True
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


class PDFProcessThread(QThread):
    """PDF处理线程"""
    progress_signal = pyqtSignal(str)  # 进度信息
    content_signal = pyqtSignal(str)   # 流式内容
    finished_signal = pyqtSignal(str)  # 完成信号
    error_signal = pyqtSignal(str)     # 错误信号
    
    def __init__(self, file_path, agent, typing_delay):
        super().__init__()
        self.file_path = file_path
        self.agent = agent
        self.typing_delay = typing_delay
        self.is_stopped = False
    
    def stop(self):
        """停止处理"""
        self.is_stopped = True
        if self.agent:
            self.agent.stop_stream()
    
    def run(self):
        """运行线程"""
        try:
            # 重置代理状态
            self.agent.reset_stream()
            
            # 设置流式回调
            self.agent.set_streaming_callback(self.content_signal.emit)
            
            # 提取PDF文本
            self.progress_signal.emit("📖 正在读取PDF文件...")
            pdf_text = self.extract_pdf_text()
            
            if self.is_stopped:
                return
                
            if not pdf_text.strip():
                self.error_signal.emit("PDF文件为空或无法提取文本内容")
                return
            
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
            self.progress_signal.emit("🤖 AI正在进行流式总结...")
            summary = self.agent.stream_step(prompt, typing_delay=self.typing_delay)
            
            if not self.agent.stop_streaming:
                self.finished_signal.emit("✅ 流式总结完成！")
            else:
                self.finished_signal.emit("⏹️ 流式总结已停止")
                
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def extract_pdf_text(self):
        """提取PDF文本内容"""
        try:
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                total_pages = len(pdf_reader.pages)
                for page_num in range(total_pages):
                    if self.is_stopped:
                        break
                        
                    self.progress_signal.emit(f"📖 读取 {page_num+1}/{total_pages} 页")
                    
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                    
                    time.sleep(0.1)
                
                return text.strip()
                
        except Exception as e:
            raise Exception(f"PDF读取失败: {str(e)}")


class PDFSummarizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF智能总结器 - PyQt6版")
        self.setGeometry(100, 100, 1000, 800)
        
        # 设置样式 - 所有文本颜色改为黑色
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                color: black;
            }
            QPushButton {
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                opacity: 0.8;
            }
            QPushButton:pressed {
                opacity: 0.6;
            }
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                font-family: "Microsoft YaHei";
                font-size: 10pt;
                color: black;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: black;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: black;
            }
        """)
        
        # 初始化变量
        self.file_path = ""
        self.current_summary = ""
        self.total_chars_streamed = 0
        self.is_streaming = False
        self.pdf_thread = None
        
        # 初始化流式AI代理
        self.setup_streaming_agent()
        
        # 创建界面
        self.init_ui()
    
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
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"初始化流式AI代理失败: {str(e)}")
            self.agent = None
    
    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("🤖 PDF智能总结器 - PyQt6版本")
        title_font = QFont("Microsoft YaHei", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: black;")  # 明确设置为黑色
        main_layout.addWidget(title_label)
        
        # API状态 - 改为黑色
        self.api_status_label = QLabel("🟢 API连接正常" if self.agent else "🔴 API连接失败")
        api_font = QFont("Microsoft YaHei", 9)
        self.api_status_label.setFont(api_font)
        self.api_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.api_status_label.setStyleSheet("color: black;")  # 改为黑色
        main_layout.addWidget(self.api_status_label)
        
        # 文件选择区域
        file_group = QGroupBox("📁 文件选择")
        file_layout = QHBoxLayout(file_group)
        
        self.file_label = QLabel("📄 未选择文件")
        self.file_label.setStyleSheet("color: black;")  # 设置为黑色
        file_layout.addWidget(self.file_label)
        
        file_layout.addStretch()
        
        select_btn = QPushButton("📁 选择PDF文件")
        select_btn.setStyleSheet("background-color: #3498db; color: white;")
        select_btn.clicked.connect(self.select_file)
        file_layout.addWidget(select_btn)
        
        main_layout.addWidget(file_group)
        
        # 控制区域
        control_group = QGroupBox("🎮 控制面板")
        control_layout = QVBoxLayout(control_group)
        
        # 按钮行
        button_layout = QHBoxLayout()
        
        self.summarize_btn = QPushButton("🚀 开始流式总结")
        self.summarize_btn.setStyleSheet("background-color: #27ae60; color: white;")
        self.summarize_btn.clicked.connect(self.start_summarization)
        self.summarize_btn.setEnabled(False)
        button_layout.addWidget(self.summarize_btn)
        
        self.stop_btn = QPushButton("⏹️ 停止生成")
        self.stop_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        self.stop_btn.clicked.connect(self.stop_summarization)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("🗑️ 清空结果")
        self.clear_btn.setStyleSheet("background-color: #95a5a6; color: white;")
        self.clear_btn.clicked.connect(self.clear_result)
        button_layout.addWidget(self.clear_btn)
        
        self.regenerate_btn = QPushButton("🔄 重新生成")
        self.regenerate_btn.setStyleSheet("background-color: #f39c12; color: white;")
        self.regenerate_btn.clicked.connect(self.regenerate_summary)
        self.regenerate_btn.setEnabled(False)
        button_layout.addWidget(self.regenerate_btn)
        
        button_layout.addStretch()
        control_layout.addLayout(button_layout)
        
        # 速度控制
        speed_layout = QHBoxLayout()
        speed_label = QLabel("⚡ 输出速度:")
        speed_label.setStyleSheet("color: black;")  # 设置为黑色
        speed_layout.addWidget(speed_label)
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 100)  # 1-100ms
        self.speed_slider.setValue(10)  # 默认10ms (0.01s)
        self.speed_slider.setToolTip("调节AI输出速度")
        speed_layout.addWidget(self.speed_slider)
        
        speed_desc_label = QLabel("(慢 ← → 快)")
        speed_desc_label.setStyleSheet("color: black;")  # 设置为黑色
        speed_layout.addWidget(speed_desc_label)
        speed_layout.addStretch()
        control_layout.addLayout(speed_layout)
        
        main_layout.addWidget(control_group)
        
        # 状态区域
        status_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        self.realtime_status = QLabel("")
        self.realtime_status.setStyleSheet("color: black; font-weight: bold;")  # 改为黑色
        status_layout.addWidget(self.realtime_status)
        
        main_layout.addLayout(status_layout)
        
        # 状态标签
        self.status_label = QLabel("📋 请选择PDF文件开始智能总结")
        self.status_label.setStyleSheet("color: black; font-size: 12pt;")  # 改为黑色
        main_layout.addWidget(self.status_label)
        
        # 结果显示区域
        result_group = QGroupBox("📝 总结结果")
        result_layout = QVBoxLayout(result_group)
        
        # 结果头部
        result_header = QHBoxLayout()
        result_info = QLabel("AI实时流式生成：")
        result_info.setStyleSheet("font-weight: bold; color: black;")  # 改为黑色
        result_header.addWidget(result_info)
        
        result_header.addStretch()
        
        self.word_count_label = QLabel("字数: 0")
        self.word_count_label.setStyleSheet("color: black;")  # 改为黑色
        result_header.addWidget(self.word_count_label)
        
        result_layout.addLayout(result_header)
        
        # 文本显示区域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(300)
        result_layout.addWidget(self.result_text)
        
        main_layout.addWidget(result_group)
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 保存总结")
        self.save_btn.setStyleSheet("background-color: #9b59b6; color: white;")
        self.save_btn.clicked.connect(self.save_summary)
        self.save_btn.setEnabled(False)
        bottom_layout.addWidget(self.save_btn)
        
        self.copy_btn = QPushButton("📋 复制到剪贴板")
        self.copy_btn.setStyleSheet("background-color: #34495e; color: white;")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setEnabled(False)
        bottom_layout.addWidget(self.copy_btn)
        
        bottom_layout.addStretch()
        main_layout.addLayout(bottom_layout)
    
    def select_file(self):
        """选择PDF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        
        if file_path:
            self.file_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.setText(f"📄 已选择: {filename}")
            if self.agent:
                self.summarize_btn.setEnabled(True)
                self.regenerate_btn.setEnabled(True)
            self.status_label.setText("✅ 文件已选择，点击开始流式总结")
    
    def start_summarization(self):
        """开始流式总结"""
        if not self.agent:
            QMessageBox.critical(self, "错误", "AI代理未初始化，请检查API配置")
            return
        
        if not self.file_path:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
        
        # 重置状态
        self.is_streaming = True
        self.total_chars_streamed = 0
        self.current_summary = ""
        
        # 更新UI状态
        self.update_ui_for_start()
        
        # 获取输出延迟（将滑块值转换为秒）
        typing_delay = self.speed_slider.value() / 1000.0
        
        # 创建并启动PDF处理线程
        self.pdf_thread = PDFProcessThread(self.file_path, self.agent, typing_delay)
        self.pdf_thread.progress_signal.connect(self.update_progress)
        self.pdf_thread.content_signal.connect(self.on_streaming_content)
        self.pdf_thread.finished_signal.connect(self.on_summarization_complete)
        self.pdf_thread.error_signal.connect(self.handle_error)
        self.pdf_thread.start()
    
    def update_ui_for_start(self):
        """更新开始时的UI状态"""
        self.status_label.setText("📖 正在读取PDF文件...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.summarize_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.regenerate_btn.setEnabled(False)
        self.realtime_status.setText("准备中...")
        
        # 清空之前的结果
        self.result_text.clear()
        self.current_summary = ""
        self.total_chars_streamed = 0
        self.word_count_label.setText("字数: 0")
    
    def update_progress(self, message):
        """更新进度信息"""
        self.status_label.setText(message)
    
    def on_streaming_content(self, content):
        """处理流式内容"""
        # 更新文本显示
        cursor = self.result_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(content)
        self.result_text.setTextCursor(cursor)
        self.result_text.ensureCursorVisible()
        
        # 更新当前总结内容
        self.current_summary += content
        self.total_chars_streamed += len(content)
        
        # 更新字数统计
        word_count = len(self.current_summary.replace(' ', '').replace('\n', ''))
        self.word_count_label.setText(f"字数: {word_count}")
        
        # 更新实时状态
        self.realtime_status.setText(f"已生成 {self.total_chars_streamed} 字符")
    
    def on_summarization_complete(self, message):
        """总结完成处理"""
        self.status_label.setText(message)
        self.realtime_status.setText("✨ 已完成")
        self.progress_bar.setVisible(False)
        self.summarize_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.regenerate_btn.setEnabled(True)
        
        if self.current_summary.strip():
            self.save_btn.setEnabled(True)
            self.copy_btn.setEnabled(True)
        
        self.is_streaming = False
    
    def stop_summarization(self):
        """停止流式总结"""
        if self.pdf_thread:
            self.pdf_thread.stop()
        self.stop_btn.setEnabled(False)
        self.status_label.setText("⏹️ 正在停止...")
        self.realtime_status.setText("停止中...")
    
    def regenerate_summary(self):
        """重新生成总结"""
        if self.is_streaming:
            QMessageBox.warning(self, "警告", "请先停止当前的生成过程")
            return
        
        if not self.file_path:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
        
        self.start_summarization()
    
    def clear_result(self):
        """清空结果"""
        if self.is_streaming:
            QMessageBox.warning(self, "警告", "请先停止当前的总结过程")
            return
        
        self.result_text.clear()
        self.current_summary = ""
        self.total_chars_streamed = 0
        self.word_count_label.setText("字数: 0")
        self.save_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
        self.status_label.setText("🗑️ 结果已清空")
        self.realtime_status.setText("")
    
    def handle_error(self, error_message):
        """处理错误"""
        self.progress_bar.setVisible(False)
        self.summarize_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.regenerate_btn.setEnabled(True)
        self.status_label.setText("❌ 总结失败")
        self.realtime_status.setText("出错了")
        self.is_streaming = False
        QMessageBox.critical(self, "错误", error_message)
    
    def copy_to_clipboard(self):
        """复制到剪贴板"""
        if not self.current_summary.strip():
            QMessageBox.warning(self, "警告", "没有可复制的内容")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_summary)
        QMessageBox.information(self, "成功", "📋 总结内容已复制到剪贴板！")
    
    def save_summary(self):
        """保存总结结果"""
        if not self.current_summary.strip():
            QMessageBox.warning(self, "警告", "没有可保存的总结内容")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存总结",
            "",
            "Markdown文件 (*.md);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(f"# 📄 PDF文档智能总结报告\n\n")
                    file.write(f"---\n\n")
                    file.write(f"**📁 原文件**: {os.path.basename(self.file_path)}\n\n")
                    file.write(f"**⏰ 总结时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    word_count = len(self.current_summary.replace(' ', '').replace('\n', ''))
                    file.write(f"📊 总结字数: {word_count}\n\n")
                    file.write(f"**🤖 生成方式**: AI流式实时生成\n\n")
                    file.write(f"---\n\n")
                    file.write(f"## 📋 总结内容\n\n")
                    file.write(self.current_summary)
                    file.write(f"\n\n---\n\n")
                    file.write(f"*本总结由AI流式生成，生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
                
                QMessageBox.information(self, "成功", f"✅ 总结已保存到:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")


def main():
    """主函数"""
    # 检查API配置
    if not my_api_key or not my_base_url or not my_model_name:
        print("⚠️  请设置正确的API配置")
        print("请在代码顶部修改以下变量:")
        print("- my_api_key: 你的API密钥")
        print("- my_base_url: API基础URL")  
        print("- my_model_name: 模型名称")
    
    # app = QApplication(sys.argv)
    # app.setApplicationName("PDF智能总结器")
    # app.setApplicationVersion("2.0")
    
    # 设置应用图标（如果有的话）
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = PDFSummarizerApp()
    window.show()
    
    print("🚀 PDF智能总结器启动成功!")
    print("✨ 核心功能:")
    print("   - 真实API流式输出")
    print("   - 可调节输出速度")
    print("   - 随时停止/重新生成")
    print("   - 实时字数统计")
    print("   - 一键复制和保存")
    print("   - Markdown格式导出")
    
    # try:
    #     sys.exit(app.exec())
    # except KeyboardInterrupt:
    #     print("\n❌ 程序被用户中断")
    # except Exception as e:
    #     print(f"💥 程序运行出错: {e}")


if __name__ == "__main__":
    main()