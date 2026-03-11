from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEventLoop
import sys


class Kiwoom(QAxWidget):

    def __init__(self):
        super().__init__()

        print("DEBUG: Kiwoom init")

        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.tr_slot)

        self.login_event_loop = QEventLoop()
        self.tr_event_loop = QEventLoop()

        self.login()

    # 로그인
    def login(self):

        print("DEBUG: CommConnect")
        self.dynamicCall("CommConnect()")

        self.login_event_loop.exec_()

    # 로그인 결과
    def login_slot(self, err_code):

        print("DEBUG: login result:", err_code)

        accounts = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        print("DEBUG: accounts:", accounts)

        account_list = [a for a in accounts.split(';') if a]

        for i, acc in enumerate(account_list):
            print(f"계좌 {i}:", acc)

        self.account = account_list[0]
        self.account = '0000'

        self.login_event_loop.exit()

        self.request_deposit()

    # 국내 예수금 조회
    def request_deposit(self):

        print("DEBUG: request domestic deposit")

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")

        ret = self.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "예수금조회",
            "opw00001",
            0,
            "1000"
        )

        print("DEBUG: CommRqData return:", ret)

        self.tr_event_loop.exec_()

    # TR 응답
    def tr_slot(self, screen, rqname, trcode, recordname, prevnext):

        print("\n===== TR 수신 =====")
        print("rqname:", rqname)
        print("trcode:", trcode)

        if rqname == "예수금조회":

            deposit = self.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                recordname,
                0,
                "예수금"
            ).strip()

            orderable = self.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                recordname,
                0,
                "주문가능금액"
            ).strip()

            withdrawable = self.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                recordname,
                0,
                "출금가능금액"
            ).strip()

            print("예수금:", deposit)
            print("주문가능금액:", orderable)
            print("출금가능금액:", withdrawable)

        print("===== TR 종료 =====\n")

        self.tr_event_loop.exit()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    kiwoom = Kiwoom()

    sys.exit(app.exec_())