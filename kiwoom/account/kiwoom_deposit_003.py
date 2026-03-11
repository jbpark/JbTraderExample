from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEventLoop
import sys


class Kiwoom(QAxWidget):

    def __init__(self):
        super().__init__()

        print("DEBUG: Kiwoom init")

        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        # 이벤트 연결
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.tr_slot)

        # 이벤트 루프
        self.login_event_loop = QEventLoop()
        self.tr_event_loop = QEventLoop()

        self.login()

    # 로그인 요청
    def login(self):

        print("DEBUG: CommConnect 호출")

        self.dynamicCall("CommConnect()")

        self.login_event_loop.exec_()

    # 로그인 결과
    def login_slot(self, err_code):

        print("DEBUG: login_slot")
        print("로그인 결과:", err_code)

        accounts = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")

        print("DEBUG: ACCNO =", accounts)

        account_list = [a for a in accounts.split(';') if a]

        for i, acc in enumerate(account_list):
            print(f"계좌 {i} :", acc)

        self.account = account_list[0]
        account = '000000'

        print("DEBUG: 사용할 계좌:", self.account)

        self.login_event_loop.exit()

        # TR 테스트
        self.request_foreign_deposit()

    # 해외주식 예수금 조회
    def request_foreign_deposit(self):

        print("DEBUG: request_foreign_deposit")

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "통화코드", "USD")

        print("DEBUG: TR 요청 opw30009")

        ret = self.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "해외예수금조회",
            "opw30009",
            0,
            "1000"
        )

        print("DEBUG: CommRqData return =", ret)

        if ret != 0:
            print("ERROR: TR 요청 실패")

        self.tr_event_loop.exec_()

    # TR 응답
    def tr_slot(self, screen, rqname, trcode, recordname, prevnext):

        print("\n========== TR 수신 ==========")
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

        print("========== TR 종료 ==========\n")

        self.tr_event_loop.exit()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    kiwoom = Kiwoom()

    sys.exit(app.exec_())