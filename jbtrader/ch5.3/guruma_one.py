import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi
from PyQt5.QtCore import QEventLoop
from PyQt5.QAxContainer import QAxWidget


class Kiwoom(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("guruma_one.ui", self)

        # 키움 API 연결
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kiwoom.OnEventConnect.connect(self.on_event_connect)

        self.login()

    def login(self):
        self.kiwoom.dynamicCall("CommConnect()")
        self.event_loop = QEventLoop()
        self.event_loop.exec_()

    def on_event_connect(self, err_code):
        if err_code == 0:
            server_type = self.kiwoom.dynamicCall("GetLoginInfo(QString)", ["GetServerGubun"])
            if server_type == "1":
                self.logTextEdit.append("모의 투자 서버 연결 성공")
            else:
                self.logTextEdit.append("실 서버 연결 성공")

            self.get_account_info()
        else:
            self.logTextEdit.append("API 연결 실패")
        self.event_loop.exit()

    def get_account_info(self):
        accounts = self.kiwoom.dynamicCall("GetLoginInfo(QString)", ["ACCNO"])
        account_list = accounts.strip().split(';')
        self.accountComboBox.addItems(account_list)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Kiwoom()
    window.show()
    sys.exit(app.exec_())
