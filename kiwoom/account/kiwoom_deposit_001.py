from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
import sys

class Kiwoom(QAxWidget):

    def __init__(self):
        super().__init__()

        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.tr_slot)

        self.dynamicCall("CommConnect()")

    def login_slot(self, err_code):
        print("로그인 성공")

        accounts = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        print("accounts:", accounts)

        # account = accounts.split(';')[0]
        account = '0000'

        print("계좌:", account)

        self.request_foreign_deposit(account)

    def request_foreign_deposit(self, account):

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "통화코드", "USD")

        self.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "해외주식예수금조회",
            "opw30009",
            0,
            "0101"
        )

    def tr_slot(self, screen, rqname, trcode, recordname, prevnext):

        if rqname == "해외주식예수금조회":

            deposit = self.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                rqname,
                0,
                "외화예수금"
            ).strip()

            orderable = self.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                rqname,
                0,
                "외화주문가능금액"
            ).strip()

            print("달러 예수금:", deposit)
            print("주문가능금액:", orderable)


app = QApplication(sys.argv)
kiwoom = Kiwoom()
app.exec_()