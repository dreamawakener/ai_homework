import sys
from PyQt6.QtWidgets import QApplication,QMainWindow,QLabel,QWidget,QLineEdit,QPushButton,QVBoxLayout,QGraphicsColorizeEffect
from Ui_mainwindow import Ui_MainWindow
# from PyQt6.QtGui import QFont


class MyMainWindow(QMainWindow,Ui_MainWindow):
    def __init__(self,parent =None):
        super(MyMainWindow,self).__init__(parent)
        self.setupUi(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置应用程序属性
    app.setApplicationName("智能学术写作系统")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Academic Tools")
    # 设置全局样式
    app.setStyle('Fusion')  # 使用Fusion样式获得更好的外观
    # app.setFont(QFont("Arial", 9))
    main_window = MyMainWindow()
    main_window.show()
    # 启动应用
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("应用程序被用户中断")
    except Exception as e:
        print(f"应用程序运行错误: {e}")