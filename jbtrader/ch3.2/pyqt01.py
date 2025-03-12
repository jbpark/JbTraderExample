import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 버튼 생성 및 설정
        self.btn = QPushButton('시스템 트레이딩', self)
        self.btn.setGeometry(50, 50, 200, 50)  # 위치 (x, y) 및 크기 (width, height) 설정
        self.btn.clicked.connect(self.showMessage)  # 버튼 클릭 시 showMessage 함수 실행

        # 창 설정
        self.setWindowTitle('PyQt5 버튼 예제')
        self.setGeometry(300, 300, 300, 200)  # 창의 위치 및 크기 설정
        self.show()

    def showMessage(self):
        # 메시지 박스 출력
        QMessageBox.information(self, '알림', '시스템 트레이딩 화이팅!')


if __name__ == '__main__':
    app = QApplication(sys.argv)  # QApplication 객체 생성
    ex = MyApp()  # MyApp 인스턴스 생성 및 실행
    sys.exit(app.exec_())  # 이벤트 루프 실행
