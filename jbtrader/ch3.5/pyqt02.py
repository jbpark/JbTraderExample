import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QDialog


# UI 파일 로드
class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("pyqt02.ui", self)

        # UI 파일에서 Push Button 과 Text Edit 위젯 찾기
        self.pushButton.clicked.connect(self.on_button_click)

    def on_button_click(self):
        self.textEdit.setText("System Trading")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MyDialog()
    dialog.show()
    sys.exit(app.exec_())