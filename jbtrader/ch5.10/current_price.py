import sys
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pandas as pd
import threading


# 현재가 tr요청으로 받기

class btl_system():
    def __init__(self):
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        self.kiwoom.OnEventConnect.connect(self.login_Connect)
        self.kiwoom.OnReceiveTrData.connect(self.trdata_get)

        print("로그인 중입니다.")
        self.kiwoom.dynamicCall("CommConnect()")

        # 로그인 이벤트 연결
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

        self.current_price_gubun = {'stock_code': [], 'current_price1': []}

        global interesting_lists
        interesting_lists = ["005930", "009450", "067160", "214420"]

    def login_Connect(self, nErrCode):
        if nErrCode == 0:
            print('로그인 성공했습니다!')
        else:
            print('로그인 실패했습니다!')
        self.login_event_loop.exit()

    def rq_data_opt10001(self, stock_code):
        print("27줄에서 입력받은 종목코드를 키움서버에 요청합니다.")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "opt_10001", "opt10001", 0, "0303")
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def trdata_get(self, sScrNo, rqname, strcode, sRecordName, sPreNext, nDataLength, sErrorCode, sMessage, sSplmMsg):
        if rqname == "opt_10001":
            stock_code = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", "opt10001", "주식기본정보요청",
                                                 0, "종목코드")
            current_price1 = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", "opt10001",
                                                     "주식기본정보요청", 0, "현재가")

            stock_code = stock_code.strip()
            current_price1 = abs(int(current_price1))
            # print(stock_code)  # 결과값 출력하는 곳
            # print(current_price1)  # 결과값 출력하는 곳

            self.current_price_gubun['stock_code'].append(stock_code)
            self.current_price_gubun['current_price1'].append(current_price1)
        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    btl = btl_system()


    def current_price24():
        for interesting_list in interesting_lists:
            btl.rq_data_opt10001(interesting_list)

            df_current_price_gubun = pd.DataFrame(btl.current_price_gubun, columns=['stock_code', 'current_price1'])
            df_current_price_gubun = df_current_price_gubun.tail(n=1)
            print(df_current_price_gubun)
        threading.Timer(10, current_price24).start()


    current_price24()
    app.exec_()