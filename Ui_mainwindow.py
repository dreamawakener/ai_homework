#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能学术写作系统 - 主界面
优化后的现代化GUI设计
"""

import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget, 
                            QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QFrame, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPalette, QLinearGradient, QBrush, QColor, QPainter

# 导入子窗口模块
from Ui_AcademicIntegrityChecker import AIC
from Ui_StreamingPaperWritingSystem import SPWS
import PDFSummarizerApp
from PDFSummarizerApp import PDFSummarizerApp

# 导入配置管理
from config import get_api_key, get_base_url, get_model_name

my_api_key = get_api_key()
my_base_url = get_base_url()
my_model_name = get_model_name()


class AnimatedButton(QPushButton):
    """带动画效果的自定义按钮"""
    
    def __init__(self, text, icon_text="", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.icon_text = icon_text
        self.original_size = None
        self.animation = None
        self.setupButton()
    
    def setupButton(self):
        """设置按钮样式和属性"""
        self.setMinimumSize(280, 60)
        self.setMaximumSize(320, 70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)
    
    def enterEvent(self, event):
        """鼠标进入事件 - 添加悬停动画"""
        self.animateButton(1.05)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件 - 恢复原始大小"""
        self.animateButton(1.0)
        super().leaveEvent(event)
    
    def animateButton(self, scale_factor):
        """按钮缩放动画"""
        if self.animation:
            self.animation.stop()
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        current_rect = self.geometry()
        center = current_rect.center()
        
        new_width = int(current_rect.width() * scale_factor)
        new_height = int(current_rect.height() * scale_factor)
        
        new_rect = QRect(0, 0, new_width, new_height)
        new_rect.moveCenter(center)
        
        self.animation.setStartValue(current_rect)
        self.animation.setEndValue(new_rect)
        self.animation.start()


class ModernTitleLabel(QLabel):
    """现代化标题标签"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setupLabel()
    
    def setupLabel(self):
        """设置标签样式"""
        font = QFont("Microsoft YaHei", 24, QFont.Weight.Bold)
        self.setFont(font)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加文字阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(1, 1)
        self.setGraphicsEffect(shadow)


class StatusIndicator(QLabel):
    """API状态指示器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupIndicator()
        self.updateStatus()
    
    def setupIndicator(self):
        """设置指示器样式"""
        self.setFixedHeight(30)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Microsoft YaHei", 10)
        self.setFont(font)
    
    def updateStatus(self):
        """更新API连接状态"""
        if all([my_api_key, my_base_url, my_model_name]):
            self.setText("🟢 API配置正常 - 系统就绪")
            self.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                    border-radius: 15px;
                    padding: 5px 15px;
                }
            """)
        else:
            self.setText("🔴 API配置异常 - 请检查配置")
            self.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                    border-radius: 15px;
                    padding: 5px 15px;
                }
            """)


class FeatureCard(QFrame):
    """功能卡片组件"""
    
    clicked = pyqtSignal()
    
    def __init__(self, title, description, icon, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.icon = icon
        self.setupCard()
    
    def setupCard(self):
        """设置卡片样式和布局"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedSize(250, 120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置卡片样式
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 10px;
            }
            QFrame:hover {
                border: 2px solid #4CAF50;
                background-color: #f9f9f9;
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # 图标和标题行
        title_layout = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 20))
        title_layout.addWidget(icon_label)
        
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # 描述文本
        desc_label = QLabel(self.description)
        desc_label.setFont(QFont("Microsoft YaHei", 9))
        desc_label.setStyleSheet("color: #666666;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addStretch()
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class AICMainWindow(QMainWindow, AIC):
    """学术诚信检查窗口"""
    def __init__(self, parent=None):
        super(AICMainWindow, self).__init__(parent)
        self.setupUi(self)


class SPWSMainWindow(QMainWindow, SPWS):
    """流式论文写作系统窗口"""
    def __init__(self, parent=None):
        super(SPWSMainWindow, self).__init__(parent)
        self.setupUi(self)


class Ui_MainWindow(object):
    """主窗口UI类"""
    
    def setupUi(self, MainWindow):
        """设置UI界面"""
        self.MainWindow = MainWindow
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(900, 700)
        MainWindow.setMinimumSize(800, 600)
        
        # 设置窗口标题和图标
        MainWindow.setWindowTitle("智能学术写作系统")
        
        # 设置整体样式
        self.setMainWindowStyle(MainWindow)
        
        # 创建中央部件
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)
        
        # 创建主布局
        self.setupMainLayout()
        
        # 创建菜单栏和状态栏
        self.setupMenuAndStatusBar(MainWindow)
        
        # 连接信号和槽
        self.connectSignals()
        
        # 应用翻译
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
    
    def setMainWindowStyle(self, MainWindow):
        """设置主窗口样式"""
        MainWindow.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f4f8, stop:1 #e2e8f0);
            }
            QMenuBar {
                background-color: #2d3748;
                color: white;
                padding: 4px;
                border: none;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
                margin: 2px;
                border-radius: 3px;
            }
            QMenuBar::item:selected {
                background-color: #4a5568;
            }
            QStatusBar {
                background-color: #2d3748;
                color: white;
                border: none;
            }
        """)
    
    def setupMainLayout(self):
        """设置主要布局"""
        # 主垂直布局
        main_layout = QVBoxLayout(self.centralwidget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)
        
        # 添加顶部间隔
        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        # 标题区域
        self.createTitleSection(main_layout)
        
        # 状态指示器
        self.createStatusSection(main_layout)
        
        # 功能按钮区域
        self.createFunctionSection(main_layout)
        
        # 底部间隔
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
    
    def createTitleSection(self, parent_layout):
        """创建标题区域"""
        title_layout = QVBoxLayout()
        title_layout.setSpacing(10)
        
        # 主标题
        self.title_label = ModernTitleLabel("🎓 智能学术写作系统")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #2d3748;
                margin: 10px 0;
            }
        """)
        title_layout.addWidget(self.title_label)
        
        # 副标题
        subtitle = QLabel("AI驱动的学术研究与写作辅助平台")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Microsoft YaHei", 12))
        subtitle.setStyleSheet("""
            QLabel {
                color: #4a5568;
                margin-bottom: 10px;
            }
        """)
        title_layout.addWidget(subtitle)
        
        parent_layout.addLayout(title_layout)
    
    def createStatusSection(self, parent_layout):
        """创建状态显示区域"""
        status_layout = QHBoxLayout()
        status_layout.addStretch()
        
        self.status_indicator = StatusIndicator()
        status_layout.addWidget(self.status_indicator)
        
        status_layout.addStretch()
        parent_layout.addLayout(status_layout)
    
    def createFunctionSection(self, parent_layout):
        """创建功能区域"""
        # 功能说明标题
        function_title = QLabel("📋 选择功能模块")
        function_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        function_title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        function_title.setStyleSheet("color: #2d3748; margin-bottom: 10px;")
        parent_layout.addWidget(function_title)
        
        # 使用网格布局放置功能卡片
        cards_layout = QGridLayout()
        cards_layout.setSpacing(20)
        cards_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建功能卡片
        self.spws_card = FeatureCard(
            "协作写作系统",
            "师生协作写作平台\n集成爬虫推荐文献功能",
            "✍️"
        )
        
        self.pdf_card = FeatureCard(
            "PDF智能总结",
            "AI驱动的PDF文档\n智能分析与总结工具",
            "📄"
        )
        
        self.aic_card = FeatureCard(
            "学术诚信检查",
            "学术诚信检测系统\n智能写作辅助工具",
            "🔍"
        )
        
        # 添加卡片到网格布局
        cards_layout.addWidget(self.spws_card, 0, 0, Qt.AlignmentFlag.AlignCenter)
        cards_layout.addWidget(self.pdf_card, 0, 2, Qt.AlignmentFlag.AlignCenter)
        cards_layout.addWidget(self.aic_card, 0, 1, Qt.AlignmentFlag.AlignCenter)
        
        # 创建容器框架
        cards_container = QFrame()
        cards_container.setLayout(cards_layout)
        cards_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                margin: 10px;
            }
        """)
        
        parent_layout.addWidget(cards_container)
        
        # 替代方案：传统按钮（可选）
        self.createTraditionalButtons(parent_layout)
    
    def createTraditionalButtons(self, parent_layout):
        """创建传统样式按钮（备用方案）"""
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("QFrame { color: #cbd5e0; margin: 10px 0; }")
        parent_layout.addWidget(separator)
        
        # 传统按钮说明
        traditional_title = QLabel("或使用传统按钮:")
        traditional_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        traditional_title.setFont(QFont("Microsoft YaHei", 10))
        traditional_title.setStyleSheet("color: #718096; margin: 5px;")
        parent_layout.addWidget(traditional_title)
        
        # 按钮布局
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)
        buttons_layout.setContentsMargins(50, 10, 50, 10)
        
        # 创建现代化按钮
        self.pushButton1 = self.createModernButton(
            "✍️ 师生协作写作 + 爬虫推荐文献", 
            "#4CAF50"
        )
        self.pushButton2 = self.createModernButton(
            "📄 PDF智能总结器", 
            "#2196F3"
        )
        self.pushButton3 = self.createModernButton(
            "🔍 学术诚信检查 + 写作助手", 
            "#FF9800"
        )
        
        buttons_layout.addWidget(self.pushButton1)
        buttons_layout.addWidget(self.pushButton2)
        buttons_layout.addWidget(self.pushButton3)
        
        parent_layout.addLayout(buttons_layout)
    
    def createModernButton(self, text, color):
        """创建现代化样式按钮"""
        button = AnimatedButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {self.darken_color(color)});
                color: white;
                border: none;
                border-radius: 25px;
                font: bold 12px "Microsoft YaHei";
                padding: 15px 20px;
                text-align: center;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.lighten_color(color)}, stop:1 {color});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.darken_color(color)}, stop:1 {self.darken_color(color, 0.3)});
            }}
        """)
        return button
    
    def darken_color(self, color, factor=0.2):
        """使颜色变暗"""
        color_map = {
            "#4CAF50": "#45a049",
            "#2196F3": "#1976D2", 
            "#FF9800": "#F57C00"
        }
        return color_map.get(color, color)
    
    def lighten_color(self, color, factor=0.2):
        """使颜色变亮"""
        color_map = {
            "#4CAF50": "#66BB6A",
            "#2196F3": "#42A5F5",
            "#FF9800": "#FFB74D"
        }
        return color_map.get(color, color)
    
    def setupMenuAndStatusBar(self, MainWindow):
        """设置菜单栏和状态栏"""
        # 菜单栏
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 900, 22))
        self.menubar.setObjectName("menubar")
        
        # 添加菜单项
        file_menu = self.menubar.addMenu("文件(&F)")
        file_menu.addAction("退出", MainWindow.close)
        
        help_menu = self.menubar.addMenu("帮助(&H)")
        help_menu.addAction("关于", self.show_about)
        
        MainWindow.setMenuBar(self.menubar)
        
        # 状态栏
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.showMessage("系统就绪 | 欢迎使用智能学术写作系统")
        MainWindow.setStatusBar(self.statusbar)
    
    def connectSignals(self):
        """连接信号和槽"""
        # 功能卡片信号连接
        self.spws_card.clicked.connect(self.open_new_window_SPWS)
        self.pdf_card.clicked.connect(self.open_new_window_PDFSummarizer)
        self.aic_card.clicked.connect(self.open_new_window_AIC)
        
        # 传统按钮信号连接
        self.pushButton1.clicked.connect(self.open_new_window_SPWS)
        self.pushButton2.clicked.connect(self.open_new_window_PDFSummarizer)
        self.pushButton3.clicked.connect(self.open_new_window_AIC)
    
    def retranslateUi(self, MainWindow):
        """设置UI文本（翻译支持）"""
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "智能学术写作系统"))
    
    def show_about(self):
        """显示关于对话框"""
        QtWidgets.QMessageBox.about(
            self.MainWindow,
            "关于",
            "智能学术写作系统 v2.0\n\n"
            "一个基于AI的学术研究与写作辅助平台\n"
            "集成了协作写作、文档总结、学术诚信检查等功能\n\n"
            "开发者: dreamawakener\n"
            "基于: PyQt6 + OpenAI API"
        )
    
    def open_new_window_SPWS(self):
        """打开师生协作写作系统"""
        try:
            self.new_window = SPWSMainWindow()
            self.new_window.show()
            self.statusbar.showMessage("已打开协作写作系统")
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self.MainWindow, 
                "错误", 
                f"无法打开协作写作系统: {str(e)}"
            )
    
    def open_new_window_PDFSummarizer(self):
        """打开PDF总结器"""
        try:
            self.new_window = PDFSummarizerApp()
            self.new_window.show()
            self.statusbar.showMessage("已打开PDF智能总结器")
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self.MainWindow, 
                "错误", 
                f"无法打开PDF总结器: {str(e)}"
            )
    
    def open_new_window_AIC(self):
        """打开学术诚信检查系统"""
        try:
            self.new_window = AICMainWindow()
            self.new_window.show()
            self.statusbar.showMessage("已打开学术诚信检查系统")
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self.MainWindow, 
                "错误", 
                f"无法打开学术诚信检查系统: {str(e)}"
            )


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # 设置窗口属性
        self.setWindowFlags(Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("智能学术写作系统")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Academic Tools")
    
    # 设置全局样式
    app.setStyle('Fusion')  # 使用Fusion样式获得更好的外观
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 启动应用
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("应用程序被用户中断")
    except Exception as e:
        print(f"应用程序运行错误: {e}")


if __name__ == "__main__":
    main()