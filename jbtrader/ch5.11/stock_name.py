import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import QEventLoop
from pykiwoom.kiwoom import Kiwoom


class KiwoomApp(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("guruma_one.ui", self)  # UI 파일 로드

        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect()  # 키움 API 연결

        # 이벤트 처리 연결
        self.kiwoom.OnEventConnect = self.on_event_connect  # 연결 이벤트 핸들러

        self.stockCode.editingFinished.connect(self.update_stock_name)

    def on_event_connect(self, err_code):
        """
        키움 API 연결 이벤트 처리
        실서버와 모의서버에 따른 로그 메시지를 출력함
        """
        if err_code == 0:
            server_type = self.kiwoom.GetLoginInfo("GetServerGubun")
            if server_type == "1":
                self.logTextEdit.append("모의 투자 서버 연결 성공")
            else:
                self.logTextEdit.append("실 서버 연결 성공")

            # 계좌 정보 가져오기
            self.update_account_info()
        else:
            QMessageBox.critical(self, "오류", "키움 API 연결 실패")

    def update_account_info(self):
        """
        계좌 정보를 가져와서 accountComboBox에 출력
        """
        accounts = self.kiwoom.GetLoginInfo("ACCNO").split(';')
        self.accountComboBox.clear()
        self.accountComboBox.addItems([acc.strip() for acc in accounts if acc.strip()])

    def update_stock_name(self):
        """
        stockCode에 입력된 종목 코드에 따라 stockName을 자동으로 설정
        """
        code = self.stockCode.text().strip()
        if code:
            stock_name = self.kiwoom.GetMasterCodeName(code)
            self.stockName.setText(stock_name)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KiwoomApp()
    window.show()
    sys.exit(app.exec_())
