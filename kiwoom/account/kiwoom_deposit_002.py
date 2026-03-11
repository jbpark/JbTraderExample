from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
import sys


class Kiwoom(QAxWidget):

    def __init__(self):
        super().__init__()

        print("DEBUG: Kiwoom init")

        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        # 이벤트 연결
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.tr_slot)

        print("DEBUG: 이벤트 연결 완료")

        print("DEBUG: 로그인 시도")
        self.dynamicCall("CommConnect()")

    # 로그인 결과
    def login_slot(self, err_code):

        print("DEBUG: login_slot 호출")
        print("로그인 결과:", err_code)

        accounts = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")

        print("DEBUG: accounts raw =", accounts)

        account_list = accounts.split(';')

        print("DEBUG: 계좌 리스트")

        for acc in account_list:
            if acc.strip():
                print("계좌:", acc)

        account = account_list[0]
        account = '0000'

        print("DEBUG: 사용할 계좌:", account)

        self.request_foreign_deposit(account)

    # TR 요청
    def request_foreign_deposit(self, account):

        print("DEBUG: request_foreign_deposit 호출")

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "통화코드", "USD")

        print("DEBUG: SetInputValue 완료")

        ret = self.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "해외예수금조회",
            "opw30009",
            0,
            "1000"
        )

        print("DEBUG: CommRqData return =", ret)

    # TR 응답
    def tr_slot(self, screen, rqname, trcode, recordname, prevnext):

        print("DEBUG: tr_slot 호출됨")

        print("screen:", screen)
        print("rqname:", rqname)
        print("trcode:", trcode)
        print("recordname:", recordname)
        print("prevnext:", prevnext)

        if rqname == "해외예수금조회":

            deposit = self.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                recordname,
                0,
                "외화예수금"
            ).strip()

            orderable = self.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                recordname,
                0,
                "외화주문가능금액"
            ).strip()

            print("달러 예수금:", deposit)
            print("주문가능금액:", orderable)


app = QApplication(sys.argv)

print("DEBUG: QApplication 시작")

kiwoom = Kiwoom()

print("DEBUG: 이벤트 루프 시작")

app.exec_()