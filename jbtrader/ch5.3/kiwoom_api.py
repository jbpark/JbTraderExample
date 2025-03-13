import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

class KiwoomAPI(QAxWidget):
    def __init__(self):
        super().__init__()

        # 키움 OpenAPI Control 설정
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        # 로그인 이벤트 루프
        self.loginLoop = QEventLoop()

        # 로그인 이벤트 핸들러 등록
        self.OnEventConnect.connect(self.event_connect)

    def login(self):
        """ 키움증권 API 로그인 """
        self.dynamicCall("CommConnect()")  # 로그인 실행
        self.loginLoop.exec_()  # 로그인 완료될 때까지 대기

    def event_connect(self, return_code):
        """ 로그인 이벤트 핸들러 """
        if return_code == 0:  # 로그인 성공
            server_type = self.dynamicCall("GetLoginInfo(QString)", "GetServerGubun")
            if server_type == "1":
                print("모의 투자 서버 연결 성공")
            else:
                print("실 서버 연결 성공")
        else:
            print("로그인 실패, 코드:", return_code)

        # 로그인 루프 종료
        self.loginLoop.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)  # PyQt5 애플리케이션 실행
    kiwoom = KiwoomAPI()
    kiwoom.login()
    sys.exit(app.exec_())  # 이벤트 루프 실행
