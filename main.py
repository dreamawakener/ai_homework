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
    # app.setFont(QFont("Arial", 9))
    main_window = MyMainWindow()
    main_window.show()
    sys.exit(app.exec())